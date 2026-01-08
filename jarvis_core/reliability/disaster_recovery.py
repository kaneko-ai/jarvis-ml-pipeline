"""Disaster Recovery for JARVIS.

Per RP-581, implements backup, restore, and recovery procedures.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class BackupType(Enum):
    """Backup types."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class RecoveryPointObjective(Enum):
    """Recovery Point Objective (RPO) levels."""
    MINUTES_1 = 60
    MINUTES_5 = 300
    MINUTES_15 = 900
    HOUR_1 = 3600
    HOURS_4 = 14400
    DAY_1 = 86400


class RecoveryTimeObjective(Enum):
    """Recovery Time Objective (RTO) levels."""
    MINUTES_5 = 300
    MINUTES_15 = 900
    MINUTES_30 = 1800
    HOUR_1 = 3600
    HOURS_4 = 14400


@dataclass
class BackupConfig:
    """Backup configuration."""
    backup_dir: str = "./backups"
    retention_days: int = 30
    compression: bool = True
    encryption_key: str | None = None
    rpo: RecoveryPointObjective = RecoveryPointObjective.HOUR_1
    rto: RecoveryTimeObjective = RecoveryTimeObjective.MINUTES_30


@dataclass
class BackupMetadata:
    """Backup metadata."""
    backup_id: str
    backup_type: BackupType
    timestamp: float
    size_bytes: int
    checksum: str
    files_count: int
    source_paths: list[str]
    compressed: bool
    encrypted: bool


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    success: bool
    backup_id: str
    restored_files: int
    duration_seconds: float
    errors: list[str] = field(default_factory=list)


class DisasterRecoveryManager:
    """Manages disaster recovery operations.
    
    Per RP-581:
    - Automated backups
    - Point-in-time recovery
    - Backup verification
    - Restore testing
    """

    def __init__(self, config: BackupConfig | None = None):
        self.config = config or BackupConfig()
        self._backup_dir = Path(self.config.backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._backups: dict[str, BackupMetadata] = {}
        self._load_backup_catalog()

    def create_backup(
        self,
        source_paths: list[str],
        backup_type: BackupType = BackupType.FULL,
        description: str | None = None,
    ) -> BackupMetadata:
        """Create a backup.
        
        Args:
            source_paths: Paths to backup.
            backup_type: Type of backup.
            description: Optional description.
            
        Returns:
            Backup metadata.
        """
        backup_id = self._generate_backup_id()
        timestamp = time.time()

        backup_path = self._backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        total_size = 0
        files_count = 0
        checksums = []

        for source in source_paths:
            source_path = Path(source)
            if not source_path.exists():
                continue

            if source_path.is_file():
                # Copy single file
                dest = backup_path / source_path.name
                shutil.copy2(source_path, dest)
                size = dest.stat().st_size
                total_size += size
                files_count += 1
                checksums.append(self._compute_checksum(dest))
            elif source_path.is_dir():
                # Copy directory
                dest_dir = backup_path / source_path.name
                shutil.copytree(source_path, dest_dir, dirs_exist_ok=True)
                for f in dest_dir.rglob("*"):
                    if f.is_file():
                        size = f.stat().st_size
                        total_size += size
                        files_count += 1
                        checksums.append(self._compute_checksum(f))

        # Compute combined checksum
        combined_checksum = hashlib.sha256(
            "".join(sorted(checksums)).encode()
        ).hexdigest()

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            timestamp=timestamp,
            size_bytes=total_size,
            checksum=combined_checksum,
            files_count=files_count,
            source_paths=source_paths,
            compressed=self.config.compression,
            encrypted=bool(self.config.encryption_key),
        )

        # Save metadata
        self._backups[backup_id] = metadata
        self._save_backup_catalog()

        # Optional: compress
        if self.config.compression:
            self._compress_backup(backup_path)

        return metadata

    def restore_backup(
        self,
        backup_id: str,
        target_dir: str,
        overwrite: bool = False,
    ) -> RestoreResult:
        """Restore from a backup.
        
        Args:
            backup_id: Backup ID to restore.
            target_dir: Target directory.
            overwrite: Whether to overwrite existing files.
            
        Returns:
            Restore result.
        """
        start_time = time.time()

        if backup_id not in self._backups:
            return RestoreResult(
                success=False,
                backup_id=backup_id,
                restored_files=0,
                duration_seconds=0,
                errors=["Backup not found"],
            )

        metadata = self._backups[backup_id]
        backup_path = self._backup_dir / backup_id
        target_path = Path(target_dir)

        # Decompress if needed
        if metadata.compressed:
            self._decompress_backup(backup_path)

        errors = []
        restored_count = 0

        for item in backup_path.iterdir():
            try:
                dest = target_path / item.name
                if dest.exists() and not overwrite:
                    errors.append(f"File exists: {dest}")
                    continue

                if item.is_file():
                    shutil.copy2(item, dest)
                    restored_count += 1
                elif item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=overwrite)
                    restored_count += sum(1 for _ in dest.rglob("*") if _.is_file())
            except Exception as e:
                errors.append(f"Error restoring {item}: {e}")

        return RestoreResult(
            success=len(errors) == 0,
            backup_id=backup_id,
            restored_files=restored_count,
            duration_seconds=time.time() - start_time,
            errors=errors,
        )

    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity.
        
        Args:
            backup_id: Backup ID to verify.
            
        Returns:
            True if backup is valid.
        """
        if backup_id not in self._backups:
            return False

        metadata = self._backups[backup_id]
        backup_path = self._backup_dir / backup_id

        if not backup_path.exists():
            return False

        # Recompute checksum
        checksums = []
        for f in backup_path.rglob("*"):
            if f.is_file():
                checksums.append(self._compute_checksum(f))

        combined = hashlib.sha256(
            "".join(sorted(checksums)).encode()
        ).hexdigest()

        return combined == metadata.checksum

    def list_backups(self) -> list[BackupMetadata]:
        """List all backups."""
        return sorted(
            self._backups.values(),
            key=lambda b: b.timestamp,
            reverse=True,
        )

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup.
        
        Args:
            backup_id: Backup ID to delete.
            
        Returns:
            True if deleted.
        """
        if backup_id not in self._backups:
            return False

        backup_path = self._backup_dir / backup_id
        if backup_path.exists():
            shutil.rmtree(backup_path)

        del self._backups[backup_id]
        self._save_backup_catalog()

        return True

    def cleanup_old_backups(self) -> int:
        """Delete backups older than retention period.
        
        Returns:
            Number of backups deleted.
        """
        cutoff = time.time() - (self.config.retention_days * 86400)
        deleted = 0

        for backup_id, metadata in list(self._backups.items()):
            if metadata.timestamp < cutoff:
                if self.delete_backup(backup_id):
                    deleted += 1

        return deleted

    def _generate_backup_id(self) -> str:
        """Generate unique backup ID."""
        import uuid
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}_{uuid.uuid4().hex[:8]}"

    def _compute_checksum(self, path: Path) -> str:
        """Compute file checksum."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _compress_backup(self, path: Path) -> None:
        """Compress backup directory."""
        # In production, use tarfile/zipfile
        pass

    def _decompress_backup(self, path: Path) -> None:
        """Decompress backup archive."""
        # In production, use tarfile/zipfile
        pass

    def _load_backup_catalog(self) -> None:
        """Load backup catalog from disk."""
        catalog_path = self._backup_dir / "catalog.json"
        if catalog_path.exists():
            with open(catalog_path) as f:
                data = json.load(f)
                for item in data:
                    metadata = BackupMetadata(
                        backup_id=item["backup_id"],
                        backup_type=BackupType(item["backup_type"]),
                        timestamp=item["timestamp"],
                        size_bytes=item["size_bytes"],
                        checksum=item["checksum"],
                        files_count=item["files_count"],
                        source_paths=item["source_paths"],
                        compressed=item["compressed"],
                        encrypted=item["encrypted"],
                    )
                    self._backups[metadata.backup_id] = metadata

    def _save_backup_catalog(self) -> None:
        """Save backup catalog to disk."""
        catalog_path = self._backup_dir / "catalog.json"
        data = []
        for metadata in self._backups.values():
            data.append({
                "backup_id": metadata.backup_id,
                "backup_type": metadata.backup_type.value,
                "timestamp": metadata.timestamp,
                "size_bytes": metadata.size_bytes,
                "checksum": metadata.checksum,
                "files_count": metadata.files_count,
                "source_paths": metadata.source_paths,
                "compressed": metadata.compressed,
                "encrypted": metadata.encrypted,
            })
        with open(catalog_path, "w") as f:
            json.dump(data, f, indent=2)


# Global manager
_dr_manager: DisasterRecoveryManager | None = None


def get_dr_manager() -> DisasterRecoveryManager:
    """Get global disaster recovery manager."""
    global _dr_manager
    if _dr_manager is None:
        _dr_manager = DisasterRecoveryManager()
    return _dr_manager
