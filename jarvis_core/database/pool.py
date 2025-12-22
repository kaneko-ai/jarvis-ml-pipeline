"""Database Connection Pool.

Per RP-550, implements connection pooling.
"""
from __future__ import annotations

import time
import threading
import queue
from dataclasses import dataclass
from typing import Optional, Any, Callable
from contextlib import contextmanager


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    
    min_size: int = 2
    max_size: int = 10
    max_overflow: int = 5
    timeout: float = 30.0
    recycle_seconds: float = 3600.0
    health_check_interval: float = 60.0


@dataclass
class PoolStats:
    """Pool statistics."""
    
    pool_size: int
    checked_out: int
    overflow: int
    available: int
    total_connections: int
    total_checkouts: int
    total_recycles: int
    avg_checkout_time_ms: float


class PooledConnection:
    """A pooled connection wrapper."""
    
    def __init__(
        self,
        connection: Any,
        pool: 'ConnectionPool',
        created_at: float,
    ):
        self.connection = connection
        self.pool = pool
        self.created_at = created_at
        self.last_used = time.time()
        self.in_use = False
    
    def is_expired(self, recycle_seconds: float) -> bool:
        """Check if connection should be recycled."""
        return time.time() - self.created_at > recycle_seconds
    
    def close(self) -> None:
        """Release back to pool."""
        self.pool.release(self)


class ConnectionPool:
    """Database connection pool.
    
    Per RP-550:
    - Pool size tuning
    - Timeout handling
    - Health checks
    - Metrics
    """
    
    def __init__(
        self,
        create_fn: Callable[[], Any],
        close_fn: Callable[[Any], None],
        health_fn: Optional[Callable[[Any], bool]] = None,
        config: Optional[PoolConfig] = None,
    ):
        self.create_fn = create_fn
        self.close_fn = close_fn
        self.health_fn = health_fn
        self.config = config or PoolConfig()
        
        self._pool: queue.Queue[PooledConnection] = queue.Queue()
        self._overflow_count = 0
        self._checked_out = 0
        self._total_connections = 0
        self._total_checkouts = 0
        self._total_recycles = 0
        self._checkout_times: list = []
        self._lock = threading.Lock()
        
        # Initialize minimum connections
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize pool with minimum connections."""
        for _ in range(self.config.min_size):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new connection."""
        try:
            raw_conn = self.create_fn()
            self._total_connections += 1
            return PooledConnection(
                connection=raw_conn,
                pool=self,
                created_at=time.time(),
            )
        except Exception:
            return None
    
    def _is_healthy(self, conn: PooledConnection) -> bool:
        """Check connection health."""
        if self.health_fn:
            try:
                return self.health_fn(conn.connection)
            except Exception:
                return False
        return True
    
    @contextmanager
    def acquire(self):
        """Acquire a connection from the pool.
        
        Yields:
            Connection object.
        """
        start = time.time()
        conn = self._checkout()
        checkout_time = (time.time() - start) * 1000
        self._checkout_times.append(checkout_time)
        
        if len(self._checkout_times) > 100:
            self._checkout_times = self._checkout_times[-100:]
        
        try:
            yield conn.connection
        finally:
            self.release(conn)
    
    def _checkout(self) -> PooledConnection:
        """Check out a connection."""
        with self._lock:
            # Try to get from pool
            try:
                conn = self._pool.get_nowait()
                
                # Check if expired
                if conn.is_expired(self.config.recycle_seconds):
                    self._recycle(conn)
                    return self._checkout()
                
                # Health check
                if not self._is_healthy(conn):
                    self._close_connection(conn)
                    return self._checkout()
                
                conn.in_use = True
                self._checked_out += 1
                self._total_checkouts += 1
                return conn
                
            except queue.Empty:
                pass
            
            # Create new if under limit
            total = self._pool.qsize() + self._checked_out + self._overflow_count
            
            if total < self.config.max_size:
                conn = self._create_connection()
                if conn:
                    conn.in_use = True
                    self._checked_out += 1
                    self._total_checkouts += 1
                    return conn
            
            # Use overflow
            if self._overflow_count < self.config.max_overflow:
                conn = self._create_connection()
                if conn:
                    conn.in_use = True
                    self._overflow_count += 1
                    self._total_checkouts += 1
                    return conn
        
        # Wait for connection
        try:
            conn = self._pool.get(timeout=self.config.timeout)
            conn.in_use = True
            
            with self._lock:
                self._checked_out += 1
                self._total_checkouts += 1
            
            return conn
        except queue.Empty:
            raise TimeoutError("Connection pool exhausted")
    
    def release(self, conn: PooledConnection) -> None:
        """Release a connection back to pool."""
        conn.in_use = False
        conn.last_used = time.time()
        
        with self._lock:
            self._checked_out -= 1
            
            # Check if overflow connection
            if self._pool.qsize() >= self.config.max_size:
                self._close_connection(conn)
                self._overflow_count = max(0, self._overflow_count - 1)
                return
        
        # Return to pool
        if conn.is_expired(self.config.recycle_seconds):
            self._recycle(conn)
        else:
            self._pool.put(conn)
    
    def _recycle(self, conn: PooledConnection) -> None:
        """Recycle a connection."""
        self._close_connection(conn)
        self._total_recycles += 1
        
        new_conn = self._create_connection()
        if new_conn:
            self._pool.put(new_conn)
    
    def _close_connection(self, conn: PooledConnection) -> None:
        """Close a connection."""
        try:
            self.close_fn(conn.connection)
        except Exception:
            pass
    
    def get_stats(self) -> PoolStats:
        """Get pool statistics."""
        with self._lock:
            avg_time = (
                sum(self._checkout_times) / len(self._checkout_times)
                if self._checkout_times else 0
            )
            
            return PoolStats(
                pool_size=self._pool.qsize(),
                checked_out=self._checked_out,
                overflow=self._overflow_count,
                available=self._pool.qsize(),
                total_connections=self._total_connections,
                total_checkouts=self._total_checkouts,
                total_recycles=self._total_recycles,
                avg_checkout_time_ms=avg_time,
            )
    
    def close_all(self) -> None:
        """Close all connections."""
        while True:
            try:
                conn = self._pool.get_nowait()
                self._close_connection(conn)
            except queue.Empty:
                break
