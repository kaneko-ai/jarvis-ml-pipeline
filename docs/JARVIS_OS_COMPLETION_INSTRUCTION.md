# JARVIS Research OS 完遂指示書
## antigravity向け実行計画書 v1.0

> **Authority**: INSTRUCTION (実行レベル)  
> **Repository**: https://github.com/kaneko-ai/jarvis-ml-pipeline  
> **Created**: 2026-01-07  
> **Target**: 120/100点 (1200/1000) 達成  
> **Estimated Duration**: 8週間 (40営業日)

---

## 目次

1. [実行前提条件](#1-実行前提条件)
2. [スキルフレームワーク活用ガイド](#2-スキルフレームワーク活用ガイド)
3. [Phase 1: オフラインモード完成](#3-phase-1-オフラインモード完成-80点)
4. [Phase 2: 埋め込み・検索完成](#4-phase-2-埋め込み検索完成-46点)
5. [Phase 3: 差別化機能完成](#5-phase-3-差別化機能完成-100点)
6. [Phase 4: エコシステム完成](#6-phase-4-エコシステム完成-96点)
7. [検証・品質保証](#7-検証品質保証)
8. [完了判定基準](#8-完了判定基準)

---

## 1. 実行前提条件

### 1.1 環境セットアップ

```bash
# リポジトリクローン
git clone https://github.com/kaneko-ai/jarvis-ml-pipeline.git
cd jarvis-ml-pipeline

# 依存関係インストール
uv sync --all-extras

# 開発用依存関係
uv sync --group dev

# Ollamaインストール確認
ollama --version || echo "Ollamaをインストールしてください: https://ollama.com/"

# モデルプル
ollama pull llama3.2:8b
ollama pull mistral:7b
```

### 1.2 スキル参照パス

```
skills/
├── BRAIN.md      # 要件定義
├── SPEC.md       # 実装計画
├── TDD.md        # テスト駆動開発
├── ORCH.md       # オーケストレーション
├── VERIFY.md     # 検証
├── REVIEW.md     # レビュー
├── FINISH.md     # 統合
├── DBG.md        # デバッグ
├── WORKTREE.md   # 並行作業
└── PARA.md       # 並列実行
```

### 1.3 実行フロー標準

```
各タスクの実行フロー:
1. BRAIN → 要件確認（このドキュメントの該当セクション参照）
2. SPEC → 2-5分タスクに分解済み（下記参照）
3. WORKTREE → 隔離ブランチ作成
4. ORCH → TDD + VERIFY でサブタスク実行
5. REVIEW → 仕様適合 + 品質チェック
6. FINISH → マージまたはPR作成
```

---

## 2. スキルフレームワーク活用ガイド

### 2.1 本指示書の使い方

```yaml
指示書構造:
  - 各Phaseは独立して実行可能
  - 各タスクは SPEC.md 形式で2-5分粒度に分解済み
  - 依存関係がある場合は明記
  - 期待出力と検証コマンドを各タスクに記載

実行パターン:
  新機能開発: BRAIN(スキップ可) → SPEC(本書参照) → WORKTREE → ORCH(TDD+VERIFY) → REVIEW → FINISH
  バグ修正: DBG → TDD → VERIFY → REVIEW → FINISH
  並行作業: PARA で複数タスクを同時進行
```

### 2.2 コミット規約

```
feat: 新機能追加
fix: バグ修正
refactor: リファクタリング
test: テスト追加
docs: ドキュメント更新
chore: その他

例: feat(offline): implement graceful degradation for network loss
```

---

## 3. Phase 1: オフラインモード完成 (+80点)

### 3.1 概要

| 項目 | 値 |
|------|-----|
| 目標スコア | +80点 |
| 推定工数 | 10日 |
| 優先度 | 🔴 最高 |
| 依存関係 | network/detector.py (完了済み) |

### 3.2 タスク 1.5.1: グレースフルデグレード完成 (+15点)

#### 要件

```yaml
目的: ネットワーク切断時に機能を段階的に縮退させ、ユーザー体験を維持
成功条件:
  - オフライン時もローカルキャッシュからの検索が動作
  - 外部API呼び出しが自動的にスキップされる
  - ユーザーに縮退状態が明示される
非目標:
  - オフライン時の新規論文取得（オンライン復帰後に実行）
```

#### サブタスク

```
□ 3.2.1 DegradationLevel Enum作成 (3分)
  ファイル: jarvis_core/network/degradation.py
  内容:
    from enum import Enum
    
    class DegradationLevel(Enum):
        FULL = "full"           # 全機能利用可能
        LIMITED = "limited"     # 外部API無効、ローカルのみ
        OFFLINE = "offline"     # 完全オフライン
        CRITICAL = "critical"   # キャッシュも利用不可
  検証: python -c "from jarvis_core.network.degradation import DegradationLevel; print(DegradationLevel.FULL)"

□ 3.2.2 DegradationManager クラス作成 (5分)
  ファイル: jarvis_core/network/degradation.py (追記)
  内容:
    @dataclass
    class DegradationManager:
        _current_level: DegradationLevel = DegradationLevel.FULL
        _listeners: List[Callable] = field(default_factory=list)
        
        def get_level(self) -> DegradationLevel:
            return self._current_level
        
        def set_level(self, level: DegradationLevel) -> None:
            old_level = self._current_level
            self._current_level = level
            if old_level != level:
                self._notify_listeners(old_level, level)
        
        def add_listener(self, callback: Callable[[DegradationLevel, DegradationLevel], None]) -> None:
            self._listeners.append(callback)
        
        def _notify_listeners(self, old: DegradationLevel, new: DegradationLevel) -> None:
            for listener in self._listeners:
                listener(old, new)
  検証: pytest tests/network/test_degradation.py -v

□ 3.2.3 自動レベル判定ロジック実装 (5分)
  ファイル: jarvis_core/network/degradation.py (追記)
  内容:
    def auto_detect_level(self) -> DegradationLevel:
        from jarvis_core.network import is_online
        from jarvis_core.cache import MultiLevelCache
        
        if is_online():
            return DegradationLevel.FULL
        
        cache = MultiLevelCache()
        if cache.get_stats().total_entries > 0:
            return DegradationLevel.LIMITED
        
        return DegradationLevel.OFFLINE
  検証: ネットワーク切断状態でテスト実行

□ 3.2.4 APIクライアントラッパー作成 (5分)
  ファイル: jarvis_core/network/api_wrapper.py
  内容:
    def degradation_aware(func):
        """デコレータ: オフライン時はキャッシュフォールバック"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_degradation_manager()
            if manager.get_level() in (DegradationLevel.LIMITED, DegradationLevel.OFFLINE):
                # キャッシュから取得を試行
                cache_key = compute_cache_key(func.__name__, args, kwargs)
                cached = get_cache().get(cache_key)
                if cached:
                    return cached
                raise OfflineError(f"Offline mode: {func.__name__} unavailable")
            return func(*args, **kwargs)
        return wrapper
  検証: pytest tests/network/test_api_wrapper.py -v

□ 3.2.5 既存APIクライアントにデコレータ適用 (5分)
  ファイル: jarvis_core/sources/pubmed_client.py, semantic_scholar.py, etc.
  変更:
    @degradation_aware
    def search(self, query: str, ...) -> List[Paper]:
        ...
  検証: オフラインモードで jarvis search "test" 実行

□ 3.2.6 テスト作成 (5分)
  ファイル: tests/network/test_degradation.py
  内容:
    - test_degradation_level_enum
    - test_manager_level_change
    - test_auto_detect_online
    - test_auto_detect_offline
    - test_api_wrapper_fallback
  検証: pytest tests/network/test_degradation.py -v --cov
```

#### 期待成果物

```
jarvis_core/network/
├── __init__.py (更新: DegradationLevel, DegradationManager export追加)
├── detector.py (既存)
├── degradation.py (新規)
└── api_wrapper.py (新規)

tests/network/
├── test_detector.py (既存)
├── test_degradation.py (新規)
└── test_api_wrapper.py (新規)
```

---

### 3.3 タスク 1.5.2: --offlineフラグ実装 (+15点)

#### 要件

```yaml
目的: CLIから明示的にオフラインモードを指定可能にする
成功条件:
  - jarvis --offline search "query" が動作
  - jarvis --offline run が動作
  - オフラインモードではネットワークアクセスを試行しない
```

#### サブタスク

```
□ 3.3.1 CLIにグローバルオプション追加 (3分)
  ファイル: jarvis_cli.py
  変更:
    @click.option('--offline', is_flag=True, help='Run in offline mode (no network access)')
    @click.pass_context
    def cli(ctx, offline: bool):
        ctx.ensure_object(dict)
        ctx.obj['offline'] = offline
        if offline:
            from jarvis_core.network import DegradationManager, DegradationLevel
            manager = DegradationManager()
            manager.set_level(DegradationLevel.OFFLINE)
  検証: jarvis --offline --help

□ 3.3.2 searchコマンドにオフライン対応追加 (3分)
  ファイル: jarvis_cli.py
  変更:
    @cli.command()
    @click.pass_context
    def search(ctx, query: str, ...):
        offline = ctx.obj.get('offline', False)
        if offline:
            # ローカルインデックスのみ検索
            results = local_search(query)
        else:
            results = unified_search(query)
  検証: jarvis --offline search "machine learning"

□ 3.3.3 runコマンドにオフライン対応追加 (3分)
  ファイル: jarvis_cli.py
  変更: 同様にofflineフラグをrun_taskに伝播
  検証: jarvis --offline run --goal "test"

□ 3.3.4 オフラインモード表示追加 (2分)
  ファイル: jarvis_cli.py
  変更:
    if offline:
        click.echo(click.style("🔌 Offline Mode: Using local cache only", fg='yellow'))
  検証: jarvis --offline search "test" で黄色メッセージ表示

□ 3.3.5 環境変数対応 (2分)
  ファイル: jarvis_cli.py
  変更:
    offline = offline or os.getenv('JARVIS_OFFLINE', '').lower() == 'true'
  検証: JARVIS_OFFLINE=true jarvis search "test"

□ 3.3.6 テスト作成 (5分)
  ファイル: tests/cli/test_offline_flag.py
  内容:
    - test_offline_flag_sets_degradation_level
    - test_offline_search_uses_local_cache
    - test_offline_env_var
    - test_offline_mode_message_displayed
  検証: pytest tests/cli/test_offline_flag.py -v
```

#### 期待成果物

```
jarvis_cli.py (更新)
tests/cli/test_offline_flag.py (新規)
```

---

### 3.4 タスク 1.5.3: 同期キュー実装 (+25点)

#### 要件

```yaml
目的: オフライン時の操作をキューイングし、オンライン復帰時に実行
成功条件:
  - オフライン時のAPI呼び出しがキューに保存される
  - キューはSQLiteに永続化される
  - オンライン復帰時に自動実行される
  - 重複リクエストは統合される
```

#### サブタスク

```
□ 3.4.1 SyncQueueスキーマ定義 (3分)
  ファイル: jarvis_core/sync/schema.py
  内容:
    from dataclasses import dataclass
    from datetime import datetime
    from enum import Enum
    from typing import Any, Dict, Optional
    
    class QueueItemStatus(Enum):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
    
    @dataclass
    class QueueItem:
        id: str
        operation: str  # "search", "fetch_paper", "fetch_citations"
        params: Dict[str, Any]
        status: QueueItemStatus = QueueItemStatus.PENDING
        created_at: datetime = field(default_factory=datetime.utcnow)
        processed_at: Optional[datetime] = None
        error: Optional[str] = None
        retry_count: int = 0
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "operation": self.operation,
                "params": self.params,
                "status": self.status.value,
                "created_at": self.created_at.isoformat(),
                "processed_at": self.processed_at.isoformat() if self.processed_at else None,
                "error": self.error,
                "retry_count": self.retry_count,
            }
  検証: python -c "from jarvis_core.sync.schema import QueueItem; print(QueueItem)"

□ 3.4.2 SQLiteストレージ実装 (5分)
  ファイル: jarvis_core/sync/storage.py
  内容:
    import sqlite3
    from pathlib import Path
    from typing import List, Optional
    
    class SyncQueueStorage:
        def __init__(self, db_path: str = "~/.jarvis/sync_queue.db"):
            self.db_path = Path(db_path).expanduser()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()
        
        def _init_db(self) -> None:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id TEXT PRIMARY KEY,
                        operation TEXT NOT NULL,
                        params TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        processed_at TEXT,
                        error TEXT,
                        retry_count INTEGER DEFAULT 0
                    )
                ''')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON sync_queue(status)')
        
        def add(self, item: QueueItem) -> None:
            ...
        
        def get_pending(self, limit: int = 100) -> List[QueueItem]:
            ...
        
        def update_status(self, item_id: str, status: QueueItemStatus, error: Optional[str] = None) -> None:
            ...
        
        def remove_completed(self, older_than_days: int = 7) -> int:
            ...
  検証: pytest tests/sync/test_storage.py -v

□ 3.4.3 SyncQueueManager実装 (5分)
  ファイル: jarvis_core/sync/manager.py
  内容:
    class SyncQueueManager:
        def __init__(self):
            self.storage = SyncQueueStorage()
            self._handlers: Dict[str, Callable] = {}
        
        def register_handler(self, operation: str, handler: Callable) -> None:
            self._handlers[operation] = handler
        
        def enqueue(self, operation: str, params: Dict[str, Any]) -> str:
            # 重複チェック
            existing = self._find_duplicate(operation, params)
            if existing:
                return existing.id
            
            item = QueueItem(
                id=str(uuid.uuid4()),
                operation=operation,
                params=params,
            )
            self.storage.add(item)
            return item.id
        
        def process_queue(self, max_items: int = 10) -> List[QueueItem]:
            pending = self.storage.get_pending(limit=max_items)
            results = []
            
            for item in pending:
                handler = self._handlers.get(item.operation)
                if not handler:
                    self.storage.update_status(item.id, QueueItemStatus.FAILED, "No handler")
                    continue
                
                try:
                    self.storage.update_status(item.id, QueueItemStatus.PROCESSING)
                    handler(**item.params)
                    self.storage.update_status(item.id, QueueItemStatus.COMPLETED)
                    item.status = QueueItemStatus.COMPLETED
                except Exception as e:
                    self.storage.update_status(item.id, QueueItemStatus.FAILED, str(e))
                    item.error = str(e)
                
                results.append(item)
            
            return results
        
        def get_queue_status(self) -> Dict[str, int]:
            ...
  検証: pytest tests/sync/test_manager.py -v

□ 3.4.4 デフォルトハンドラー登録 (3分)
  ファイル: jarvis_core/sync/handlers.py
  内容:
    def register_default_handlers(manager: SyncQueueManager) -> None:
        from jarvis_core.sources import UnifiedSourceClient
        
        client = UnifiedSourceClient()
        
        manager.register_handler("search", lambda query, **kwargs: client.search(query, **kwargs))
        manager.register_handler("fetch_paper", lambda doi: client.get_by_doi(doi))
        manager.register_handler("fetch_citations", lambda paper_id: client.get_citations(paper_id))
  検証: python -c "from jarvis_core.sync.handlers import register_default_handlers"

□ 3.4.5 APIラッパーにキューイング統合 (3分)
  ファイル: jarvis_core/network/api_wrapper.py (更新)
  変更:
    def degradation_aware_with_queue(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_degradation_manager()
            if manager.get_level() in (DegradationLevel.LIMITED, DegradationLevel.OFFLINE):
                # キャッシュ確認
                cache_key = compute_cache_key(func.__name__, args, kwargs)
                cached = get_cache().get(cache_key)
                if cached:
                    return cached
                
                # キューに追加
                queue_manager = get_sync_queue_manager()
                queue_id = queue_manager.enqueue(func.__name__, {"args": args, "kwargs": kwargs})
                
                raise OfflineQueuedError(f"Queued for sync: {queue_id}")
            
            return func(*args, **kwargs)
        return wrapper
  検証: オフライン状態でAPI呼び出し→キューに追加されることを確認

□ 3.4.6 CLI同期コマンド追加 (3分)
  ファイル: jarvis_cli.py
  変更:
    @cli.command()
    def sync():
        """Process pending sync queue items."""
        from jarvis_core.sync import SyncQueueManager
        from jarvis_core.network import is_online
        
        if not is_online():
            click.echo(click.style("Cannot sync: offline", fg='red'))
            return
        
        manager = SyncQueueManager()
        results = manager.process_queue()
        
        completed = sum(1 for r in results if r.status == QueueItemStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == QueueItemStatus.FAILED)
        
        click.echo(f"Sync complete: {completed} succeeded, {failed} failed")
  検証: jarvis sync

□ 3.4.7 テスト作成 (5分)
  ファイル: tests/sync/test_queue.py
  内容:
    - test_queue_item_creation
    - test_storage_add_and_get
    - test_duplicate_detection
    - test_process_queue_success
    - test_process_queue_failure_retry
    - test_cleanup_old_items
  検証: pytest tests/sync/ -v --cov
```

#### 期待成果物

```
jarvis_core/sync/
├── __init__.py (新規)
├── schema.py (新規)
├── storage.py (新規)
├── manager.py (新規)
└── handlers.py (新規)

tests/sync/
├── test_schema.py (新規)
├── test_storage.py (新規)
├── test_manager.py (新規)
└── test_queue.py (新規)
```

---

### 3.5 タスク 1.5.4: オンライン復帰同期 (+20点)

#### 要件

```yaml
目的: ネットワーク復帰を検出し、キューを自動処理
成功条件:
  - ネットワーク復帰時に自動でキューを処理
  - バックグラウンドで非同期実行
  - 処理完了通知
```

#### サブタスク

```
□ 3.5.1 ネットワーク変更リスナー実装 (5分)
  ファイル: jarvis_core/network/listener.py
  内容:
    import threading
    import time
    from typing import Callable, List
    
    class NetworkChangeListener:
        def __init__(self, check_interval: float = 5.0):
            self._check_interval = check_interval
            self._callbacks: List[Callable[[bool], None]] = []
            self._last_status: bool = True
            self._running = False
            self._thread: Optional[threading.Thread] = None
        
        def add_callback(self, callback: Callable[[bool], None]) -> None:
            self._callbacks.append(callback)
        
        def start(self) -> None:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
        
        def stop(self) -> None:
            self._running = False
            if self._thread:
                self._thread.join(timeout=2.0)
        
        def _monitor_loop(self) -> None:
            from jarvis_core.network import is_online
            
            while self._running:
                current_status = is_online()
                
                if current_status != self._last_status:
                    for callback in self._callbacks:
                        try:
                            callback(current_status)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                    
                    self._last_status = current_status
                
                time.sleep(self._check_interval)
  検証: pytest tests/network/test_listener.py -v

□ 3.5.2 自動同期コールバック実装 (3分)
  ファイル: jarvis_core/sync/auto_sync.py
  内容:
    def on_network_restored(is_online: bool) -> None:
        if not is_online:
            return
        
        logger.info("Network restored, starting queue sync...")
        
        manager = SyncQueueManager()
        status = manager.get_queue_status()
        
        if status.get("pending", 0) == 0:
            logger.info("No pending items to sync")
            return
        
        # バックグラウンドで実行
        thread = threading.Thread(
            target=_background_sync,
            args=(manager,),
            daemon=True
        )
        thread.start()
    
    def _background_sync(manager: SyncQueueManager) -> None:
        results = manager.process_queue(max_items=50)
        completed = sum(1 for r in results if r.status == QueueItemStatus.COMPLETED)
        logger.info(f"Background sync completed: {completed} items processed")
  検証: ネットワーク切断→復帰で自動同期されることを確認

□ 3.5.3 アプリケーション起動時にリスナー登録 (3分)
  ファイル: jarvis_core/app.py
  変更:
    def init_app():
        # ... 既存のinit ...
        
        # ネットワークリスナー開始
        from jarvis_core.network.listener import NetworkChangeListener
        from jarvis_core.sync.auto_sync import on_network_restored
        
        listener = NetworkChangeListener()
        listener.add_callback(on_network_restored)
        listener.start()
        
        return listener
  検証: アプリ起動後にネットワーク変更を検出

□ 3.5.4 同期進捗表示 (3分)
  ファイル: jarvis_core/sync/progress.py
  内容:
    class SyncProgressReporter:
        def __init__(self):
            self._callbacks: List[Callable[[int, int], None]] = []
        
        def add_callback(self, callback: Callable[[int, int], None]) -> None:
            self._callbacks.append(callback)
        
        def report(self, completed: int, total: int) -> None:
            for callback in self._callbacks:
                callback(completed, total)
  検証: 同期中に進捗が報告されることを確認

□ 3.5.5 CLI同期状態表示コマンド (3分)
  ファイル: jarvis_cli.py
  変更:
    @cli.command()
    def sync_status():
        """Show sync queue status."""
        from jarvis_core.sync import SyncQueueManager
        
        manager = SyncQueueManager()
        status = manager.get_queue_status()
        
        click.echo("Sync Queue Status:")
        click.echo(f"  Pending:    {status.get('pending', 0)}")
        click.echo(f"  Processing: {status.get('processing', 0)}")
        click.echo(f"  Completed:  {status.get('completed', 0)}")
        click.echo(f"  Failed:     {status.get('failed', 0)}")
  検証: jarvis sync-status

□ 3.5.6 テスト作成 (3分)
  ファイル: tests/sync/test_auto_sync.py
  内容:
    - test_network_listener_detects_change
    - test_auto_sync_on_network_restored
    - test_background_sync_thread
    - test_progress_reporter
  検証: pytest tests/sync/test_auto_sync.py -v
```

#### 期待成果物

```
jarvis_core/network/listener.py (新規)
jarvis_core/sync/auto_sync.py (新規)
jarvis_core/sync/progress.py (新規)
tests/sync/test_auto_sync.py (新規)
tests/network/test_listener.py (新規)
```

---

### 3.6 タスク 1.5.5: オフライン状態表示 (+5点)

#### サブタスク

```
□ 3.6.1 状態バナー表示関数 (3分)
  ファイル: jarvis_core/ui/status.py
  内容:
    from jarvis_core.network import DegradationLevel, get_degradation_manager
    
    def get_status_banner() -> str:
        manager = get_degradation_manager()
        level = manager.get_level()
        
        banners = {
            DegradationLevel.FULL: "",
            DegradationLevel.LIMITED: "⚠️  Limited Mode: External APIs unavailable",
            DegradationLevel.OFFLINE: "🔌 Offline Mode: Using local cache only",
            DegradationLevel.CRITICAL: "🚨 Critical: No cache available",
        }
        
        return banners.get(level, "")
  検証: python -c "from jarvis_core.ui.status import get_status_banner; print(get_status_banner())"

□ 3.6.2 CLIに状態表示統合 (2分)
  ファイル: jarvis_cli.py
  変更: 各コマンド実行前にバナー表示
  検証: オフライン時にjarvisコマンド実行でバナー表示
```

---

## 4. Phase 2: 埋め込み・検索完成 (+46点)

### 4.1 概要

| 項目 | 値 |
|------|-----|
| 目標スコア | +46点 |
| 推定工数 | 8日 |
| 優先度 | 🟠 高 |
| 依存関係 | Phase 1完了推奨 |

### 4.2 タスク 1.2.1: SPECTER2モデル追加 (+6点)

#### サブタスク

```
□ 4.2.1 SPECTER2アダプタ作成 (5分)
  ファイル: jarvis_core/embeddings/specter2.py
  内容:
    from sentence_transformers import SentenceTransformer
    from typing import List
    import numpy as np
    
    class SPECTER2Embedding:
        """AllenAI SPECTER2 for scientific document embedding."""
        
        MODEL_NAME = "allenai/specter2"
        
        def __init__(self, device: str = "auto"):
            self._model: Optional[SentenceTransformer] = None
            self._device = device
        
        def _load_model(self) -> SentenceTransformer:
            if self._model is None:
                device = self._device
                if device == "auto":
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                
                self._model = SentenceTransformer(self.MODEL_NAME, device=device)
            return self._model
        
        def embed(self, texts: List[str]) -> np.ndarray:
            model = self._load_model()
            return model.encode(texts, show_progress_bar=False)
        
        def embed_paper(self, title: str, abstract: str) -> np.ndarray:
            """SPECTER2 recommended format: title + [SEP] + abstract"""
            text = f"{title} [SEP] {abstract}"
            return self.embed([text])[0]
        
        @property
        def dimension(self) -> int:
            return 768
  検証: pytest tests/embeddings/test_specter2.py -v

□ 4.2.2 モデル選択ロジック追加 (3分)
  ファイル: jarvis_core/embeddings/__init__.py
  変更:
    from .specter2 import SPECTER2Embedding
    
    def get_embedding_model(model_type: str = "general") -> EmbeddingModel:
        if model_type == "scientific":
            return SPECTER2Embedding()
        return SentenceTransformerEmbedding()
  検証: python -c "from jarvis_core.embeddings import get_embedding_model; print(get_embedding_model('scientific'))"

□ 4.2.3 設定ファイル対応 (2分)
  ファイル: configs/embedding_config.yml
  内容:
    embedding:
      default_model: "general"  # or "scientific"
      models:
        general:
          name: "all-MiniLM-L6-v2"
          dimension: 384
        scientific:
          name: "allenai/specter2"
          dimension: 768
  検証: 設定ファイル読み込み確認

□ 4.2.4 テスト作成 (3分)
  ファイル: tests/embeddings/test_specter2.py
  内容:
    - test_specter2_load
    - test_specter2_embed_single
    - test_specter2_embed_paper
    - test_dimension
  検証: pytest tests/embeddings/test_specter2.py -v
```

---

### 4.3 タスク 1.2.2: ハイブリッド検索完成 (+18点)

#### サブタスク

```
□ 4.3.1 BM25インデックス完成 (5分)
  ファイル: jarvis_core/embeddings/bm25.py
  追加内容:
    class BM25Index:
        def __init__(self):
            self._index: Optional[BM25Okapi] = None
            self._documents: List[str] = []
            self._doc_ids: List[str] = []
        
        def build(self, documents: List[str], doc_ids: List[str]) -> None:
            from rank_bm25 import BM25Okapi
            
            tokenized = [self._tokenize(doc) for doc in documents]
            self._index = BM25Okapi(tokenized)
            self._documents = documents
            self._doc_ids = doc_ids
        
        def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
            if self._index is None:
                raise ValueError("Index not built")
            
            tokenized_query = self._tokenize(query)
            scores = self._index.get_scores(tokenized_query)
            
            # Top-k取得
            top_indices = np.argsort(scores)[::-1][:top_k]
            return [(self._doc_ids[i], scores[i]) for i in top_indices]
        
        def _tokenize(self, text: str) -> List[str]:
            # シンプルなトークナイズ（改善可能）
            return text.lower().split()
        
        def save(self, path: str) -> None:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump({
                    'documents': self._documents,
                    'doc_ids': self._doc_ids,
                }, f)
        
        def load(self, path: str) -> None:
            import pickle
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.build(data['documents'], data['doc_ids'])
  検証: pytest tests/embeddings/test_bm25.py -v

□ 4.3.2 Reciprocal Rank Fusion実装 (5分)
  ファイル: jarvis_core/embeddings/hybrid.py
  追加内容:
    from enum import Enum
    from typing import List, Tuple, Dict
    
    class FusionMethod(Enum):
        RRF = "rrf"  # Reciprocal Rank Fusion
        WEIGHTED = "weighted"
        COMBSUM = "combsum"
    
    class HybridSearch:
        def __init__(
            self,
            dense_model: SentenceTransformerEmbedding,
            sparse_index: BM25Index,
            fusion_method: FusionMethod = FusionMethod.RRF,
            rrf_k: int = 60,
            dense_weight: float = 0.5,
        ):
            self._dense = dense_model
            self._sparse = sparse_index
            self._fusion = fusion_method
            self._rrf_k = rrf_k
            self._dense_weight = dense_weight
            self._doc_embeddings: Optional[np.ndarray] = None
            self._doc_ids: List[str] = []
        
        def index(self, documents: List[str], doc_ids: List[str]) -> None:
            # Dense embeddings
            self._doc_embeddings = self._dense.embed(documents)
            self._doc_ids = doc_ids
            
            # Sparse index
            self._sparse.build(documents, doc_ids)
        
        def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
            # Dense search
            query_embedding = self._dense.embed([query])[0]
            dense_scores = self._cosine_similarity(query_embedding, self._doc_embeddings)
            dense_results = self._rank_results(dense_scores)
            
            # Sparse search
            sparse_results = self._sparse.search(query, top_k=top_k * 2)
            
            # Fusion
            if self._fusion == FusionMethod.RRF:
                return self._rrf_fusion(dense_results, sparse_results, top_k)
            elif self._fusion == FusionMethod.WEIGHTED:
                return self._weighted_fusion(dense_results, sparse_results, top_k)
            else:
                return self._combsum_fusion(dense_results, sparse_results, top_k)
        
        def _rrf_fusion(
            self,
            dense: List[Tuple[str, float]],
            sparse: List[Tuple[str, float]],
            top_k: int
        ) -> List[Tuple[str, float]]:
            scores: Dict[str, float] = {}
            
            for rank, (doc_id, _) in enumerate(dense):
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (self._rrf_k + rank + 1)
            
            for rank, (doc_id, _) in enumerate(sparse):
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (self._rrf_k + rank + 1)
            
            sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_results[:top_k]
        
        def _cosine_similarity(self, query: np.ndarray, docs: np.ndarray) -> np.ndarray:
            query_norm = query / np.linalg.norm(query)
            docs_norm = docs / np.linalg.norm(docs, axis=1, keepdims=True)
            return np.dot(docs_norm, query_norm)
        
        def _rank_results(self, scores: np.ndarray) -> List[Tuple[str, float]]:
            indices = np.argsort(scores)[::-1]
            return [(self._doc_ids[i], scores[i]) for i in indices]
  検証: pytest tests/embeddings/test_hybrid.py -v

□ 4.3.3 インデックス永続化 (3分)
  ファイル: jarvis_core/embeddings/hybrid.py
  追加:
    def save(self, path: str) -> None:
        import json
        import numpy as np
        
        base_path = Path(path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Dense embeddings
        np.save(base_path / "dense_embeddings.npy", self._doc_embeddings)
        
        # Doc IDs
        with open(base_path / "doc_ids.json", 'w') as f:
            json.dump(self._doc_ids, f)
        
        # Sparse index
        self._sparse.save(str(base_path / "bm25_index.pkl"))
    
    def load(self, path: str) -> None:
        base_path = Path(path)
        
        self._doc_embeddings = np.load(base_path / "dense_embeddings.npy")
        
        with open(base_path / "doc_ids.json", 'r') as f:
            self._doc_ids = json.load(f)
        
        self._sparse.load(str(base_path / "bm25_index.pkl"))
  検証: インデックスの保存と読み込みテスト

□ 4.3.4 CLIにインデックス構築コマンド追加 (3分)
  ファイル: jarvis_cli.py
  追加:
    @cli.command()
    @click.argument('source_dir')
    @click.option('--output', '-o', default='~/.jarvis/index')
    def build_index(source_dir: str, output: str):
        """Build hybrid search index from papers."""
        from jarvis_core.embeddings import HybridSearch, get_embedding_model, BM25Index
        
        # 論文読み込み
        papers = load_papers_from_dir(source_dir)
        
        # インデックス構築
        hybrid = HybridSearch(
            dense_model=get_embedding_model(),
            sparse_index=BM25Index(),
        )
        
        documents = [f"{p.title} {p.abstract}" for p in papers]
        doc_ids = [p.id for p in papers]
        
        hybrid.index(documents, doc_ids)
        hybrid.save(output)
        
        click.echo(f"Index built: {len(papers)} papers -> {output}")
  検証: jarvis build-index ./papers -o ./index

□ 4.3.5 テスト作成 (5分)
  ファイル: tests/embeddings/test_hybrid.py
  内容:
    - test_hybrid_index_build
    - test_hybrid_search_rrf
    - test_hybrid_search_weighted
    - test_hybrid_save_load
    - test_fusion_method_comparison
  検証: pytest tests/embeddings/test_hybrid.py -v --cov
```

---

### 4.4 タスク 1.2.3: ベクトルストア最適化 (+12点)

#### サブタスク

```
□ 4.4.1 FAISSベクトルストア実装 (5分)
  ファイル: jarvis_core/embeddings/vector_store.py
  内容:
    import faiss
    import numpy as np
    from typing import List, Tuple, Optional
    
    class FAISSVectorStore:
        def __init__(self, dimension: int, index_type: str = "flat"):
            self._dimension = dimension
            self._index: Optional[faiss.Index] = None
            self._doc_ids: List[str] = []
            self._index_type = index_type
        
        def build(self, embeddings: np.ndarray, doc_ids: List[str]) -> None:
            if self._index_type == "flat":
                self._index = faiss.IndexFlatIP(self._dimension)
            elif self._index_type == "ivf":
                quantizer = faiss.IndexFlatIP(self._dimension)
                nlist = min(100, len(doc_ids) // 10)
                self._index = faiss.IndexIVFFlat(quantizer, self._dimension, nlist)
                self._index.train(embeddings.astype(np.float32))
            
            # 正規化してから追加
            normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            self._index.add(normalized.astype(np.float32))
            self._doc_ids = doc_ids
        
        def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            query_norm = query_norm.reshape(1, -1).astype(np.float32)
            
            distances, indices = self._index.search(query_norm, top_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:
                    results.append((self._doc_ids[idx], float(distances[0][i])))
            
            return results
        
        def save(self, path: str) -> None:
            faiss.write_index(self._index, f"{path}.faiss")
            with open(f"{path}.ids", 'w') as f:
                json.dump(self._doc_ids, f)
        
        def load(self, path: str) -> None:
            self._index = faiss.read_index(f"{path}.faiss")
            with open(f"{path}.ids", 'r') as f:
                self._doc_ids = json.load(f)
  検証: pytest tests/embeddings/test_vector_store.py -v

□ 4.4.2 インクリメンタル追加サポート (3分)
  ファイル: jarvis_core/embeddings/vector_store.py
  追加:
    def add(self, embeddings: np.ndarray, doc_ids: List[str]) -> None:
        normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        self._index.add(normalized.astype(np.float32))
        self._doc_ids.extend(doc_ids)
  検証: 追加後の検索テスト

□ 4.4.3 HybridSearchにFAISS統合 (3分)
  ファイル: jarvis_core/embeddings/hybrid.py
  変更:
    def __init__(self, ..., use_faiss: bool = True):
        if use_faiss:
            self._vector_store = FAISSVectorStore(dense_model.dimension)
        else:
            self._vector_store = None
  検証: FAISS使用時の検索テスト

□ 4.4.4 テスト作成 (3分)
  ファイル: tests/embeddings/test_vector_store.py
  検証: pytest tests/embeddings/test_vector_store.py -v
```

---

### 4.5 タスク 1.2.4: キャッシュ圧縮改善 (+10点)

#### サブタスク

```
□ 4.5.1 圧縮オプション追加 (3分)
  ファイル: jarvis_core/cache/multi_level.py
  変更:
    def __init__(self, ..., compression: str = "gzip"):
        self._compression = compression
    
    def _compress(self, data: bytes) -> bytes:
        if self._compression == "gzip":
            import gzip
            return gzip.compress(data)
        elif self._compression == "lz4":
            import lz4.frame
            return lz4.frame.compress(data)
        return data
    
    def _decompress(self, data: bytes) -> bytes:
        if self._compression == "gzip":
            import gzip
            return gzip.decompress(data)
        elif self._compression == "lz4":
            import lz4.frame
            return lz4.frame.decompress(data)
        return data
  検証: pytest tests/cache/test_compression.py -v

□ 4.5.2 LRUキャッシュ改善 (3分)
  ファイル: jarvis_core/cache/multi_level.py
  変更:
    from collections import OrderedDict
    
    class LRUCache:
        def __init__(self, max_size: int = 1000):
            self._cache = OrderedDict()
            self._max_size = max_size
        
        def get(self, key: str) -> Optional[Any]:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None
        
        def put(self, key: str, value: Any) -> None:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
            self._cache[key] = value
  検証: pytest tests/cache/test_lru.py -v

□ 4.5.3 キャッシュ統計機能強化 (2分)
  ファイル: jarvis_core/cache/multi_level.py
  追加:
    def get_detailed_stats(self) -> Dict[str, Any]:
        return {
            "l1_hits": self._l1_hits,
            "l2_hits": self._l2_hits,
            "misses": self._misses,
            "hit_rate": self._calculate_hit_rate(),
            "l1_size": len(self._l1_cache),
            "l2_size": self._get_l2_size(),
            "compression_ratio": self._calculate_compression_ratio(),
        }
  検証: python -c "from jarvis_core.cache import MultiLevelCache; print(MultiLevelCache().get_detailed_stats())"

□ 4.5.4 テスト作成 (2分)
  ファイル: tests/cache/test_compression.py, tests/cache/test_lru.py
  検証: pytest tests/cache/ -v --cov
```

---

## 5. Phase 3: 差別化機能完成 (+100点)

### 5.1 概要

| 項目 | 値 |
|------|-----|
| 目標スコア | +100点 |
| 推定工数 | 12日 |
| 優先度 | 🟡 中 |
| 依存関係 | Phase 1, 2完了推奨 |

### 5.2 タスク 2.1.1: アンサンブルグレーディング完成 (+12点)

#### サブタスク

```
□ 5.2.1 重み最適化ロジック (5分)
  ファイル: jarvis_core/evidence/ensemble.py
  追加:
    class EnsembleClassifier:
        def __init__(
            self,
            rule_weight: float = 0.4,
            llm_weight: float = 0.6,
            use_confidence_weighting: bool = True,
        ):
            self._rule_classifier = RuleBasedClassifier()
            self._llm_classifier = LLMBasedClassifier()
            self._rule_weight = rule_weight
            self._llm_weight = llm_weight
            self._use_confidence = use_confidence_weighting
        
        def classify(self, title: str, abstract: str) -> EvidenceGrade:
            rule_result = self._rule_classifier.classify(title, abstract)
            llm_result = self._llm_classifier.classify(title, abstract)
            
            if self._use_confidence:
                # 信頼度に基づく動的重み付け
                total_confidence = rule_result.confidence + llm_result.confidence
                rule_w = rule_result.confidence / total_confidence
                llm_w = llm_result.confidence / total_confidence
            else:
                rule_w = self._rule_weight
                llm_w = self._llm_weight
            
            # 加重平均でレベル決定
            level_scores = self._calculate_level_scores(rule_result, llm_result, rule_w, llm_w)
            best_level = max(level_scores, key=level_scores.get)
            
            return EvidenceGrade(
                level=best_level,
                confidence=level_scores[best_level],
                reasoning=f"Rule: {rule_result.level.value}, LLM: {llm_result.level.value}",
                method="ensemble",
            )
  検証: pytest tests/evidence/test_ensemble.py -v

□ 5.2.2 バッチグレーディング最適化 (3分)
  ファイル: jarvis_core/evidence/ensemble.py
  追加:
    def classify_batch(self, papers: List[Dict[str, str]]) -> List[EvidenceGrade]:
        # ルールベースはバッチ処理
        rule_results = [self._rule_classifier.classify(p['title'], p['abstract']) for p in papers]
        
        # LLMはバッチで効率化
        llm_results = self._llm_classifier.classify_batch(papers)
        
        return [
            self._combine_results(rule, llm)
            for rule, llm in zip(rule_results, llm_results)
        ]
  検証: バッチ処理のパフォーマンステスト

□ 5.2.3 テスト強化 (2分)
  ファイル: tests/evidence/test_ensemble.py
  検証: pytest tests/evidence/ -v --cov
```

---

### 5.3 タスク 2.1.2: 信頼度可視化 (+15点)

#### サブタスク

```
□ 5.3.1 信頼度スコア詳細出力 (3分)
  ファイル: jarvis_core/evidence/schema.py
  追加:
    @dataclass
    class DetailedEvidenceGrade(EvidenceGrade):
        rule_confidence: float = 0.0
        llm_confidence: float = 0.0
        level_probabilities: Dict[str, float] = field(default_factory=dict)
        
        def to_visualization_dict(self) -> Dict[str, Any]:
            return {
                "level": self.level.value,
                "level_description": self.level.description,
                "confidence": self.confidence,
                "components": {
                    "rule_based": self.rule_confidence,
                    "llm_based": self.llm_confidence,
                },
                "probabilities": self.level_probabilities,
            }
  検証: python -c "from jarvis_core.evidence import DetailedEvidenceGrade"

□ 5.3.2 Mermaidグラフ生成 (5分)
  ファイル: jarvis_core/evidence/visualizer.py
  内容:
    class EvidenceVisualizer:
        def generate_confidence_chart(self, grades: List[DetailedEvidenceGrade]) -> str:
            """Mermaidパイチャート生成"""
            level_counts = {}
            for grade in grades:
                level = grade.level.value
                level_counts[level] = level_counts.get(level, 0) + 1
            
            mermaid = "pie title Evidence Level Distribution\n"
            for level, count in level_counts.items():
                mermaid += f'    "{level}" : {count}\n'
            
            return mermaid
        
        def generate_confidence_bar(self, grade: DetailedEvidenceGrade) -> str:
            """単一グレードのバーチャート"""
            probs = grade.level_probabilities
            
            mermaid = "xychart-beta\n"
            mermaid += '    title "Level Probabilities"\n'
            mermaid += f'    x-axis [{", ".join(probs.keys())}]\n'
            mermaid += f'    y-axis "Probability" 0 --> 1\n'
            mermaid += f'    bar [{", ".join(str(v) for v in probs.values())}]\n'
            
            return mermaid
  検証: pytest tests/evidence/test_visualizer.py -v

□ 5.3.3 CLI可視化コマンド (3分)
  ファイル: jarvis_cli.py
  追加:
    @cli.command()
    @click.argument('paper_file')
    @click.option('--output', '-o', default='evidence_report.md')
    def grade_evidence(paper_file: str, output: str):
        """Grade evidence levels for papers and generate visualization."""
        from jarvis_core.evidence import grade_evidence, EvidenceVisualizer
        
        papers = load_papers(paper_file)
        grades = [grade_evidence(p['title'], p['abstract']) for p in papers]
        
        visualizer = EvidenceVisualizer()
        
        with open(output, 'w') as f:
            f.write("# Evidence Grading Report\n\n")
            f.write("## Distribution\n\n")
            f.write("```mermaid\n")
            f.write(visualizer.generate_confidence_chart(grades))
            f.write("```\n\n")
            
            f.write("## Details\n\n")
            for paper, grade in zip(papers, grades):
                f.write(f"### {paper['title']}\n")
                f.write(f"- Level: {grade.level.value}\n")
                f.write(f"- Confidence: {grade.confidence:.2%}\n\n")
        
        click.echo(f"Report generated: {output}")
  検証: jarvis grade-evidence papers.json -o report.md

□ 5.3.4 テスト作成 (2分)
  ファイル: tests/evidence/test_visualizer.py
  検証: pytest tests/evidence/test_visualizer.py -v
```

---

### 5.4 タスク 2.2.1: Support/Contrast分類完成 (+20点)

#### サブタスク

```
□ 5.4.1 スタンス分類器強化 (5分)
  ファイル: jarvis_core/citation/stance_classifier.py
  追加/変更:
    class CitationStance(Enum):
        SUPPORT = "support"
        CONTRAST = "contrast"
        MENTION = "mention"
        COMPARE = "compare"
        EXTEND = "extend"
        BACKGROUND = "background"
    
    class StanceClassifier:
        def __init__(self):
            self._support_patterns = [
                r"confirm", r"support", r"consistent with", r"in line with",
                r"agree", r"corroborate", r"validate", r"reinforce",
            ]
            self._contrast_patterns = [
                r"contradict", r"contrary to", r"inconsistent", r"disagree",
                r"challenge", r"refute", r"oppose", r"conflict",
            ]
            self._compare_patterns = [
                r"compared to", r"in contrast to", r"unlike", r"whereas",
                r"however", r"although", r"while",
            ]
        
        def classify(self, context: CitationContext) -> StanceClassificationResult:
            text = context.get_full_context().lower()
            
            support_score = self._match_patterns(text, self._support_patterns)
            contrast_score = self._match_patterns(text, self._contrast_patterns)
            compare_score = self._match_patterns(text, self._compare_patterns)
            
            if contrast_score > support_score and contrast_score > compare_score:
                stance = CitationStance.CONTRAST
                confidence = min(contrast_score / 3, 1.0)
            elif support_score > contrast_score and support_score > compare_score:
                stance = CitationStance.SUPPORT
                confidence = min(support_score / 3, 1.0)
            elif compare_score > 0:
                stance = CitationStance.COMPARE
                confidence = min(compare_score / 3, 1.0)
            else:
                stance = CitationStance.MENTION
                confidence = 0.5
            
            return StanceClassificationResult(
                stance=stance,
                confidence=confidence,
                reasoning=f"Pattern scores: support={support_score}, contrast={contrast_score}",
            )
        
        def _match_patterns(self, text: str, patterns: List[str]) -> int:
            return sum(1 for p in patterns if re.search(p, text))
  検証: pytest tests/citation/test_stance_classifier.py -v

□ 5.4.2 LLMベース分類器追加 (5分)
  ファイル: jarvis_core/citation/llm_stance.py
  内容:
    class LLMStanceClassifier:
        def __init__(self):
            from jarvis_core.llm import get_router
            self._router = get_router()
        
        def classify(self, context: CitationContext) -> StanceClassificationResult:
            prompt = f"""Classify the citation stance in the following context.

Context: {context.get_full_context()}

Classify as one of:
- SUPPORT: The citing paper agrees with or builds upon the cited work
- CONTRAST: The citing paper disagrees or presents conflicting findings
- MENTION: Neutral reference without strong agreement or disagreement
- COMPARE: Comparing methodologies or results

Respond with JSON: {{"stance": "...", "confidence": 0.0-1.0, "reasoning": "..."}}"""
            
            response = self._router.generate(prompt, max_tokens=200)
            return self._parse_response(response)
  検証: pytest tests/citation/test_llm_stance.py -v

□ 5.4.3 アンサンブル分類器 (3分)
  ファイル: jarvis_core/citation/stance_ensemble.py
  内容:
    class EnsembleStanceClassifier:
        def __init__(self, rule_weight: float = 0.4, llm_weight: float = 0.6):
            self._rule = StanceClassifier()
            self._llm = LLMStanceClassifier()
            self._rule_weight = rule_weight
            self._llm_weight = llm_weight
        
        def classify(self, context: CitationContext) -> StanceClassificationResult:
            rule_result = self._rule.classify(context)
            llm_result = self._llm.classify(context)
            
            # 一致していれば高信頼
            if rule_result.stance == llm_result.stance:
                confidence = min((rule_result.confidence + llm_result.confidence) / 2 + 0.2, 1.0)
                return StanceClassificationResult(
                    stance=rule_result.stance,
                    confidence=confidence,
                    reasoning=f"Consensus: {rule_result.stance.value}",
                )
            
            # LLMを優先（ただしルールの信頼度が高ければルール）
            if rule_result.confidence > 0.8:
                return rule_result
            return llm_result
  検証: pytest tests/citation/test_stance_ensemble.py -v

□ 5.4.4 テスト作成 (3分)
  ファイル: tests/citation/test_stance_*.py
  検証: pytest tests/citation/ -v --cov
```

---

### 5.5 タスク 2.2.2: 引用影響力スコア (+15点)

#### サブタスク

```
□ 5.5.1 影響力計算ロジック (5分)
  ファイル: jarvis_core/citation/influence.py
  内容:
    from dataclasses import dataclass
    from typing import Dict, List
    
    @dataclass
    class InfluenceScore:
        paper_id: str
        total_citations: int
        support_count: int
        contrast_count: int
        mention_count: int
        influence_score: float
        controversy_score: float
    
    class InfluenceCalculator:
        def __init__(self, citation_graph: CitationGraph):
            self._graph = citation_graph
        
        def calculate(self, paper_id: str) -> InfluenceScore:
            citations = self._graph.get_citations(paper_id)
            
            support = sum(1 for c in citations if c.stance == CitationStance.SUPPORT)
            contrast = sum(1 for c in citations if c.stance == CitationStance.CONTRAST)
            mention = sum(1 for c in citations if c.stance == CitationStance.MENTION)
            
            total = len(citations)
            
            # 影響力スコア: 被引用数 * (支持率 + 0.5 * 対照率)
            support_rate = support / total if total > 0 else 0
            contrast_rate = contrast / total if total > 0 else 0
            
            influence = total * (support_rate + 0.5 * contrast_rate)
            
            # 議論性スコア: 対照引用の割合
            controversy = contrast_rate
            
            return InfluenceScore(
                paper_id=paper_id,
                total_citations=total,
                support_count=support,
                contrast_count=contrast,
                mention_count=mention,
                influence_score=influence,
                controversy_score=controversy,
            )
  検証: pytest tests/citation/test_influence.py -v

□ 5.5.2 ランキング機能 (3分)
  ファイル: jarvis_core/citation/influence.py
  追加:
    def rank_papers(self, paper_ids: List[str], by: str = "influence") -> List[InfluenceScore]:
        scores = [self.calculate(pid) for pid in paper_ids]
        
        if by == "influence":
            return sorted(scores, key=lambda x: x.influence_score, reverse=True)
        elif by == "controversy":
            return sorted(scores, key=lambda x: x.controversy_score, reverse=True)
        elif by == "citations":
            return sorted(scores, key=lambda x: x.total_citations, reverse=True)
        
        return scores
  検証: pytest tests/citation/test_influence.py::test_ranking -v

□ 5.5.3 CLIコマンド追加 (2分)
  ファイル: jarvis_cli.py
  追加:
    @cli.command()
    @click.argument('paper_ids', nargs=-1)
    @click.option('--by', default='influence', type=click.Choice(['influence', 'controversy', 'citations']))
    def rank_influence(paper_ids: Tuple[str], by: str):
        """Rank papers by influence score."""
        ...
  検証: jarvis rank-influence paper1 paper2 --by influence

□ 5.5.4 テスト作成 (3分)
  ファイル: tests/citation/test_influence.py
  検証: pytest tests/citation/test_influence.py -v
```

---

### 5.6 タスク 2.3.1: 矛盾解決提案 (+20点)

#### サブタスク

```
□ 5.6.1 解決提案スキーマ (3分)
  ファイル: jarvis_core/contradiction/resolution.py
  内容:
    from dataclasses import dataclass
    from enum import Enum
    from typing import List, Optional
    
    class ResolutionStrategy(Enum):
        METHODOLOGY = "methodology"  # 方法論の違い
        POPULATION = "population"    # 対象集団の違い
        TIMEFRAME = "timeframe"      # 時期の違い
        MEASURE = "measure"          # 測定方法の違い
        CONTEXT = "context"          # コンテキストの違い
        UNKNOWN = "unknown"
    
    @dataclass
    class ResolutionSuggestion:
        strategy: ResolutionStrategy
        explanation: str
        confidence: float
        evidence_for: List[str]
        evidence_against: List[str]
        recommended_action: str
  検証: python -c "from jarvis_core.contradiction.resolution import ResolutionSuggestion"

□ 5.6.2 解決提案生成器 (5分)
  ファイル: jarvis_core/contradiction/resolver.py
  内容:
    class ContradictionResolver:
        def __init__(self):
            from jarvis_core.llm import get_router
            self._router = get_router()
        
        def suggest_resolution(
            self,
            contradiction: ContradictionResult,
            claim_a_context: str,
            claim_b_context: str,
        ) -> ResolutionSuggestion:
            prompt = f"""Analyze the contradiction and suggest resolution:

Claim A: {contradiction.claim_a.text}
Context A: {claim_a_context}

Claim B: {contradiction.claim_b.text}
Context B: {claim_b_context}

Contradiction Type: {contradiction.contradiction_type.value}

Suggest how this contradiction might be resolved. Consider:
1. Different methodologies
2. Different study populations
3. Different time periods
4. Different measurement approaches
5. Different contexts

Respond with JSON:
{{
    "strategy": "methodology|population|timeframe|measure|context|unknown",
    "explanation": "...",
    "confidence": 0.0-1.0,
    "evidence_for": ["..."],
    "evidence_against": ["..."],
    "recommended_action": "..."
}}"""
            
            response = self._router.generate(prompt, max_tokens=500)
            return self._parse_response(response)
  検証: pytest tests/contradiction/test_resolver.py -v

□ 5.6.3 ルールベース補助解決 (3分)
  ファイル: jarvis_core/contradiction/resolver.py
  追加:
    def _rule_based_suggestion(self, contradiction: ContradictionResult) -> Optional[ResolutionStrategy]:
        text_a = contradiction.claim_a.text.lower()
        text_b = contradiction.claim_b.text.lower()
        
        # 数値の違い → 測定方法
        if re.search(r'\d+%', text_a) and re.search(r'\d+%', text_b):
            return ResolutionStrategy.MEASURE
        
        # 時間表現 → 時期
        time_patterns = [r'\d{4}', r'year', r'month', r'recent']
        if any(re.search(p, text_a) for p in time_patterns):
            return ResolutionStrategy.TIMEFRAME
        
        # 集団表現 → 対象集団
        population_patterns = [r'patients?', r'subjects?', r'participants?', r'adults?', r'children']
        if any(re.search(p, text_a) for p in population_patterns):
            return ResolutionStrategy.POPULATION
        
        return None
  検証: ルールベース解決のテスト

□ 5.6.4 矛盾レポート生成 (3分)
  ファイル: jarvis_core/contradiction/report.py
  内容:
    class ContradictionReportGenerator:
        def generate(self, contradictions: List[ContradictionResult], resolutions: List[ResolutionSuggestion]) -> str:
            report = "# Contradiction Analysis Report\n\n"
            
            for i, (cont, res) in enumerate(zip(contradictions, resolutions)):
                report += f"## Contradiction {i+1}\n\n"
                report += f"**Claim A**: {cont.claim_a.text}\n"
                report += f"**Claim B**: {cont.claim_b.text}\n"
                report += f"**Type**: {cont.contradiction_type.value}\n\n"
                
                report += "### Resolution Suggestion\n\n"
                report += f"**Strategy**: {res.strategy.value}\n"
                report += f"**Explanation**: {res.explanation}\n"
                report += f"**Confidence**: {res.confidence:.0%}\n"
                report += f"**Recommended Action**: {res.recommended_action}\n\n"
                report += "---\n\n"
            
            return report
  検証: pytest tests/contradiction/test_report.py -v

□ 5.6.5 テスト作成 (3分)
  ファイル: tests/contradiction/test_resolver.py, test_report.py
  検証: pytest tests/contradiction/ -v --cov
```

---

### 5.7 タスク 2.4.1: PRISMA完全準拠 (+12点)

#### サブタスク

```
□ 5.7.1 PRISMA 2020スキーマ完全実装 (5分)
  ファイル: jarvis_core/prisma/schema.py
  追加:
    @dataclass
    class PRISMA2020Data:
        """PRISMA 2020 compliant data structure."""
        
        # Identification
        records_identified_databases: int = 0
        records_identified_registers: int = 0
        records_identified_other: int = 0
        
        # Deduplication
        records_removed_duplicates: int = 0
        records_removed_automation: int = 0
        records_removed_other: int = 0
        
        # Screening
        records_screened: int = 0
        records_excluded_screening: int = 0
        
        # Eligibility
        reports_sought_retrieval: int = 0
        reports_not_retrieved: int = 0
        reports_assessed_eligibility: int = 0
        reports_excluded_eligibility: int = 0
        exclusion_reasons: Dict[str, int] = field(default_factory=dict)
        
        # Included
        studies_included_review: int = 0
        reports_included_review: int = 0
        
        # New studies from other methods
        records_identified_citation: int = 0
        records_identified_websites: int = 0
        records_identified_organisations: int = 0
        reports_sought_citation: int = 0
        reports_not_retrieved_citation: int = 0
        reports_assessed_citation: int = 0
        reports_excluded_citation: int = 0
        
        def validate(self) -> List[str]:
            """Validate PRISMA data consistency."""
            errors = []
            
            total_identified = (
                self.records_identified_databases +
                self.records_identified_registers +
                self.records_identified_other
            )
            
            total_removed = (
                self.records_removed_duplicates +
                self.records_removed_automation +
                self.records_removed_other
            )
            
            if self.records_screened > total_identified - total_removed:
                errors.append("Screened records exceed available after deduplication")
            
            return errors
  検証: pytest tests/prisma/test_schema.py -v

□ 5.7.2 PRISMA 2020フローチャート生成 (5分)
  ファイル: jarvis_core/prisma/generator.py
  更新:
    def generate_prisma_2020_flow(self, data: PRISMA2020Data) -> str:
        """Generate PRISMA 2020 compliant flow diagram in Mermaid."""
        
        mermaid = """flowchart TD
    subgraph identification["Identification"]
        db["Records from databases<br>(n = {db})"]
        reg["Records from registers<br>(n = {reg})"]
        other["Records from other sources<br>(n = {other})"]
    end
    
    subgraph screening["Screening"]
        dup["Records removed before screening:<br>Duplicates (n = {dup})<br>Automation (n = {auto})<br>Other (n = {other_rm})"]
        screened["Records screened<br>(n = {screened})"]
        excluded_screen["Records excluded<br>(n = {excl_screen})"]
    end
    
    subgraph eligibility["Eligibility"]
        sought["Reports sought<br>(n = {sought})"]
        not_retrieved["Reports not retrieved<br>(n = {not_ret})"]
        assessed["Reports assessed<br>(n = {assessed})"]
        excluded_elig["Reports excluded:<br>{exclusion_reasons}"]
    end
    
    subgraph included["Included"]
        studies["Studies in review<br>(n = {studies})"]
        reports["Reports in review<br>(n = {reports})"]
    end
    
    db --> dup
    reg --> dup
    other --> dup
    dup --> screened
    screened --> excluded_screen
    screened --> sought
    sought --> not_retrieved
    sought --> assessed
    assessed --> excluded_elig
    assessed --> studies
    studies --> reports
""".format(
            db=data.records_identified_databases,
            reg=data.records_identified_registers,
            other=data.records_identified_other,
            dup=data.records_removed_duplicates,
            auto=data.records_removed_automation,
            other_rm=data.records_removed_other,
            screened=data.records_screened,
            excl_screen=data.records_excluded_screening,
            sought=data.reports_sought_retrieval,
            not_ret=data.reports_not_retrieved,
            assessed=data.reports_assessed_eligibility,
            exclusion_reasons=self._format_exclusion_reasons(data.exclusion_reasons),
            studies=data.studies_included_review,
            reports=data.reports_included_review,
        )
        
        return mermaid
  検証: pytest tests/prisma/test_generator.py -v

□ 5.7.3 テスト作成 (2分)
  ファイル: tests/prisma/test_prisma_2020.py
  検証: pytest tests/prisma/ -v --cov
```

---

## 6. Phase 4: エコシステム完成 (+96点)

### 6.1 概要

| 項目 | 値 |
|------|-----|
| 目標スコア | +96点 |
| 推定工数 | 10日 |
| 優先度 | 🟢 通常 |
| 依存関係 | Phase 1-3完了推奨 |

### 6.2 タスク 3.1.1: Zotero連携 (+25点)

#### サブタスク

```
□ 6.2.1 Zotero APIクライアント (5分)
  ファイル: jarvis_core/integrations/zotero.py
  内容:
    from dataclasses import dataclass
    from typing import Any, Dict, List, Optional
    import requests
    
    @dataclass
    class ZoteroConfig:
        api_key: str
        user_id: str
        library_type: str = "user"  # "user" or "group"
    
    class ZoteroClient:
        BASE_URL = "https://api.zotero.org"
        
        def __init__(self, config: ZoteroConfig):
            self._config = config
            self._headers = {
                "Zotero-API-Key": config.api_key,
                "Zotero-API-Version": "3",
            }
        
        def _get_library_url(self) -> str:
            if self._config.library_type == "user":
                return f"{self.BASE_URL}/users/{self._config.user_id}"
            return f"{self.BASE_URL}/groups/{self._config.user_id}"
        
        def get_items(self, collection_key: Optional[str] = None, limit: int = 100) -> List[Dict]:
            url = f"{self._get_library_url()}/items"
            params = {"limit": limit, "format": "json"}
            if collection_key:
                params["collection"] = collection_key
            
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
        
        def create_item(self, item_data: Dict[str, Any]) -> Dict:
            url = f"{self._get_library_url()}/items"
            response = requests.post(url, headers=self._headers, json=[item_data])
            response.raise_for_status()
            return response.json()
        
        def get_collections(self) -> List[Dict]:
            url = f"{self._get_library_url()}/collections"
            response = requests.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()
        
        def search(self, query: str, limit: int = 25) -> List[Dict]:
            url = f"{self._get_library_url()}/items"
            params = {"q": query, "limit": limit, "format": "json"}
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
  検証: pytest tests/integrations/test_zotero.py -v

□ 6.2.2 Zoteroプラグイン実装 (5分)
  ファイル: jarvis_core/plugins/zotero_plugin.py
  内容:
    from jarvis_core.plugins import PluginProtocol, PluginManifest
    from jarvis_core.integrations.zotero import ZoteroClient, ZoteroConfig
    
    class ZoteroPlugin(PluginProtocol):
        @property
        def manifest(self) -> PluginManifest:
            return PluginManifest(
                name="zotero",
                version="1.0.0",
                description="Zotero reference manager integration",
                author="JARVIS Team",
                plugin_type="integration",
            )
        
        def initialize(self, config: Dict[str, Any]) -> None:
            zotero_config = ZoteroConfig(
                api_key=config["api_key"],
                user_id=config["user_id"],
                library_type=config.get("library_type", "user"),
            )
            self._client = ZoteroClient(zotero_config)
        
        def import_references(self, collection_key: Optional[str] = None) -> List[Dict]:
            items = self._client.get_items(collection_key)
            return [self._convert_to_paper(item) for item in items]
        
        def export_references(self, papers: List[Dict], collection_key: Optional[str] = None) -> int:
            exported = 0
            for paper in papers:
                item_data = self._convert_to_zotero(paper)
                self._client.create_item(item_data)
                exported += 1
            return exported
        
        def _convert_to_paper(self, zotero_item: Dict) -> Dict:
            data = zotero_item.get("data", {})
            return {
                "id": zotero_item.get("key"),
                "title": data.get("title", ""),
                "authors": [c.get("lastName", "") for c in data.get("creators", [])],
                "abstract": data.get("abstractNote", ""),
                "doi": data.get("DOI"),
                "year": data.get("date", "")[:4] if data.get("date") else None,
                "source": "zotero",
            }
        
        def _convert_to_zotero(self, paper: Dict) -> Dict:
            return {
                "itemType": "journalArticle",
                "title": paper.get("title", ""),
                "creators": [{"creatorType": "author", "lastName": a} for a in paper.get("authors", [])],
                "abstractNote": paper.get("abstract", ""),
                "DOI": paper.get("doi"),
                "date": paper.get("year"),
            }
  検証: pytest tests/plugins/test_zotero_plugin.py -v

□ 6.2.3 CLIコマンド追加 (3分)
  ファイル: jarvis_cli.py
  追加:
    @cli.group()
    def zotero():
        """Zotero integration commands."""
        pass
    
    @zotero.command()
    @click.option('--collection', '-c', help='Zotero collection key')
    @click.option('--output', '-o', default='papers.json')
    def import_refs(collection: Optional[str], output: str):
        """Import references from Zotero."""
        from jarvis_core.plugins import get_plugin_manager
        
        manager = get_plugin_manager()
        plugin = manager.get_plugin("zotero")
        
        papers = plugin.import_references(collection)
        
        with open(output, 'w') as f:
            json.dump(papers, f, indent=2)
        
        click.echo(f"Imported {len(papers)} references to {output}")
    
    @zotero.command()
    @click.argument('papers_file')
    @click.option('--collection', '-c', help='Target Zotero collection')
    def export_refs(papers_file: str, collection: Optional[str]):
        """Export references to Zotero."""
        from jarvis_core.plugins import get_plugin_manager
        
        with open(papers_file) as f:
            papers = json.load(f)
        
        manager = get_plugin_manager()
        plugin = manager.get_plugin("zotero")
        
        count = plugin.export_references(papers, collection)
        click.echo(f"Exported {count} references to Zotero")
  検証: jarvis zotero import --collection ABC123 -o papers.json

□ 6.2.4 テスト作成 (3分)
  ファイル: tests/integrations/test_zotero.py, tests/plugins/test_zotero_plugin.py
  検証: pytest tests/integrations/test_zotero.py tests/plugins/test_zotero_plugin.py -v
```

---

### 6.3 タスク 3.1.2: Mendeley連携 (+20点)

#### サブタスク

```
□ 6.3.1 Mendeley APIクライアント (5分)
  ファイル: jarvis_core/integrations/mendeley.py
  内容:
    class MendeleyClient:
        BASE_URL = "https://api.mendeley.com"
        
        def __init__(self, access_token: str):
            self._token = access_token
            self._headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.mendeley-document.1+json",
            }
        
        def get_documents(self, folder_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
            url = f"{self.BASE_URL}/documents"
            params = {"limit": limit}
            if folder_id:
                params["folder_id"] = folder_id
            
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
        
        def create_document(self, document: Dict) -> Dict:
            url = f"{self.BASE_URL}/documents"
            response = requests.post(url, headers=self._headers, json=document)
            response.raise_for_status()
            return response.json()
        
        def search(self, query: str, limit: int = 25) -> List[Dict]:
            url = f"{self.BASE_URL}/search/catalog"
            params = {"query": query, "limit": limit}
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json()
  検証: pytest tests/integrations/test_mendeley.py -v

□ 6.3.2 Mendeleyプラグイン実装 (5分)
  ファイル: jarvis_core/plugins/mendeley_plugin.py
  内容: Zoteroプラグインと同様の構造で実装
  検証: pytest tests/plugins/test_mendeley_plugin.py -v

□ 6.3.3 CLIコマンド追加 (3分)
  ファイル: jarvis_cli.py
  追加: zoteroと同様のmendeley グループコマンド
  検証: jarvis mendeley import -o papers.json

□ 6.3.4 テスト作成 (3分)
  検証: pytest tests/integrations/test_mendeley.py -v
```

---

### 6.4 タスク 3.2.1: RIS/BibTeX完全出力 (+12点)

#### サブタスク

```
□ 6.4.1 RISフォーマッタ完成 (3分)
  ファイル: jarvis_core/export/ris.py
  内容:
    class RISExporter:
        TYPE_MAP = {
            "journal_article": "JOUR",
            "conference_paper": "CONF",
            "book": "BOOK",
            "thesis": "THES",
            "preprint": "UNPB",
        }
        
        def export(self, papers: List[Dict]) -> str:
            lines = []
            for paper in papers:
                lines.extend(self._format_paper(paper))
                lines.append("")  # Empty line between entries
            return "\n".join(lines)
        
        def _format_paper(self, paper: Dict) -> List[str]:
            lines = []
            
            paper_type = paper.get("type", "journal_article")
            lines.append(f"TY  - {self.TYPE_MAP.get(paper_type, 'JOUR')}")
            
            if paper.get("title"):
                lines.append(f"TI  - {paper['title']}")
            
            for author in paper.get("authors", []):
                lines.append(f"AU  - {author}")
            
            if paper.get("year"):
                lines.append(f"PY  - {paper['year']}")
            
            if paper.get("journal"):
                lines.append(f"JO  - {paper['journal']}")
            
            if paper.get("volume"):
                lines.append(f"VL  - {paper['volume']}")
            
            if paper.get("issue"):
                lines.append(f"IS  - {paper['issue']}")
            
            if paper.get("pages"):
                lines.append(f"SP  - {paper['pages']}")
            
            if paper.get("doi"):
                lines.append(f"DO  - {paper['doi']}")
            
            if paper.get("abstract"):
                lines.append(f"AB  - {paper['abstract']}")
            
            if paper.get("keywords"):
                for kw in paper['keywords']:
                    lines.append(f"KW  - {kw}")
            
            lines.append("ER  - ")
            
            return lines
        
        def export_to_file(self, papers: List[Dict], path: str) -> None:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.export(papers))
  検証: pytest tests/export/test_ris.py -v

□ 6.4.2 BibTeXフォーマッタ完成 (3分)
  ファイル: jarvis_core/export/bibtex.py
  内容:
    class BibTeXExporter:
        def export(self, papers: List[Dict]) -> str:
            entries = [self._format_paper(paper) for paper in papers]
            return "\n\n".join(entries)
        
        def _format_paper(self, paper: Dict) -> str:
            entry_type = self._get_entry_type(paper.get("type", "article"))
            cite_key = self._generate_cite_key(paper)
            
            fields = []
            
            if paper.get("title"):
                fields.append(f'  title = {{{paper["title"]}}}')
            
            if paper.get("authors"):
                authors_str = " and ".join(paper["authors"])
                fields.append(f'  author = {{{authors_str}}}')
            
            if paper.get("year"):
                fields.append(f'  year = {{{paper["year"]}}}')
            
            if paper.get("journal"):
                fields.append(f'  journal = {{{paper["journal"]}}}')
            
            if paper.get("volume"):
                fields.append(f'  volume = {{{paper["volume"]}}}')
            
            if paper.get("pages"):
                fields.append(f'  pages = {{{paper["pages"]}}}')
            
            if paper.get("doi"):
                fields.append(f'  doi = {{{paper["doi"]}}}')
            
            if paper.get("abstract"):
                abstract = paper["abstract"].replace("{", "\\{").replace("}", "\\}")
                fields.append(f'  abstract = {{{abstract}}}')
            
            fields_str = ",\n".join(fields)
            return f"@{entry_type}{{{cite_key},\n{fields_str}\n}}"
        
        def _get_entry_type(self, paper_type: str) -> str:
            type_map = {
                "journal_article": "article",
                "conference_paper": "inproceedings",
                "book": "book",
                "thesis": "phdthesis",
                "preprint": "misc",
            }
            return type_map.get(paper_type, "article")
        
        def _generate_cite_key(self, paper: Dict) -> str:
            first_author = paper.get("authors", ["unknown"])[0].split()[-1].lower()
            year = paper.get("year", "0000")
            title_word = paper.get("title", "untitled").split()[0].lower()
            return f"{first_author}{year}{title_word}"
  検証: pytest tests/export/test_bibtex.py -v

□ 6.4.3 統合エクスポーター (2分)
  ファイル: jarvis_core/export/__init__.py
  追加:
    from .ris import RISExporter
    from .bibtex import BibTeXExporter
    
    def export_papers(papers: List[Dict], format: str, path: str) -> None:
        if format == "ris":
            exporter = RISExporter()
        elif format == "bibtex":
            exporter = BibTeXExporter()
        else:
            raise ValueError(f"Unknown format: {format}")
        
        exporter.export_to_file(papers, path)
  検証: python -c "from jarvis_core.export import export_papers"

□ 6.4.4 CLIコマンド追加 (2分)
  ファイル: jarvis_cli.py
  追加:
    @cli.command()
    @click.argument('papers_file')
    @click.option('--format', '-f', type=click.Choice(['ris', 'bibtex', 'json']), default='bibtex')
    @click.option('--output', '-o', required=True)
    def export(papers_file: str, format: str, output: str):
        """Export papers to various formats."""
        from jarvis_core.export import export_papers
        
        with open(papers_file) as f:
            papers = json.load(f)
        
        export_papers(papers, format, output)
        click.echo(f"Exported {len(papers)} papers to {output}")
  検証: jarvis export papers.json -f bibtex -o refs.bib

□ 6.4.5 テスト作成 (2分)
  ファイル: tests/export/test_ris.py, tests/export/test_bibtex.py
  検証: pytest tests/export/ -v --cov
```

---

### 6.5 タスク 3.2.2: CLI完成 (+10点)

#### サブタスク

```
□ 6.5.1 jarvis-screen改善 (3分)
  ファイル: jarvis_core/active_learning/cli.py
  追加:
    - 進捗表示バー
    - キーボードショートカット
    - セッション保存/再開
  検証: jarvis-screen papers.json

□ 6.5.2 ヘルプメッセージ改善 (2分)
  ファイル: jarvis_cli.py
  変更: 全コマンドにexamplesと詳細helpを追加
  検証: jarvis --help, jarvis search --help

□ 6.5.3 バージョン・設定コマンド追加 (2分)
  ファイル: jarvis_cli.py
  追加:
    @cli.command()
    def version():
        """Show version information."""
        click.echo(f"JARVIS Research OS v{__version__}")
    
    @cli.command()
    def config():
        """Show current configuration."""
        from jarvis_core.config import get_config
        config = get_config()
        click.echo(yaml.dump(config, default_flow_style=False))
  検証: jarvis version, jarvis config

□ 6.5.4 テスト作成 (3分)
  ファイル: tests/cli/test_commands.py
  検証: pytest tests/cli/ -v --cov
```

---

### 6.6 タスク 3.2.3: ドキュメント完成 (+15点)

#### サブタスク

```
□ 6.6.1 APIリファレンス自動生成 (3分)
  ファイル: docs/api/README.md (自動生成)
  方法:
    pip install pdoc3
    pdoc --html jarvis_core -o docs/api
  検証: docs/api/ にHTMLが生成される

□ 6.6.2 ユーザーガイド完成 (5分)
  ファイル: docs/user_guide.md
  内容:
    - インストール手順
    - クイックスタート
    - CLI使用方法
    - API使用例
    - トラブルシューティング
  検証: docs/user_guide.md が存在し内容が完全

□ 6.6.3 開発者ガイド更新 (3分)
  ファイル: docs/developer_guide.md
  内容:
    - アーキテクチャ概要
    - モジュール説明
    - プラグイン開発方法
    - テスト方法
    - コントリビューション方法
  検証: docs/developer_guide.md 確認

□ 6.6.4 README更新 (2分)
  ファイル: README.md
  追加:
    - 全機能の説明
    - バッジ更新
    - クイックスタート例
  検証: README.md の内容確認

□ 6.6.5 CHANGELOG作成 (2分)
  ファイル: CHANGELOG.md
  内容: v1.0.0までの変更履歴
  検証: CHANGELOG.md 確認
```

---

### 6.7 タスク 3.3.1: CORE API統合 (+15点)

#### サブタスク

```
□ 6.7.1 CORE APIクライアント実装 (5分)
  ファイル: jarvis_core/sources/core_client.py
  内容:
    class COREClient:
        BASE_URL = "https://api.core.ac.uk/v3"
        
        def __init__(self, api_key: str):
            self._api_key = api_key
            self._headers = {"Authorization": f"Bearer {api_key}"}
        
        def search(self, query: str, limit: int = 10) -> List[Dict]:
            url = f"{self.BASE_URL}/search/works"
            params = {"q": query, "limit": limit}
            response = requests.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json().get("results", [])
        
        def get_work(self, core_id: str) -> Optional[Dict]:
            url = f"{self.BASE_URL}/works/{core_id}"
            response = requests.get(url, headers=self._headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        
        def get_fulltext(self, core_id: str) -> Optional[str]:
            work = self.get_work(core_id)
            if work and work.get("fullText"):
                return work["fullText"]
            return None
  検証: pytest tests/sources/test_core_client.py -v

□ 6.7.2 UnifiedSourceClientに統合 (3分)
  ファイル: jarvis_core/sources/unified_client.py
  変更:
    from .core_client import COREClient
    
    class UnifiedSourceClient:
        def __init__(self, ..., core_api_key: Optional[str] = None):
            ...
            if core_api_key:
                self._core = COREClient(core_api_key)
  検証: COREを含めた統合検索テスト

□ 6.7.3 テスト作成 (2分)
  ファイル: tests/sources/test_core_client.py
  検証: pytest tests/sources/test_core_client.py -v
```

---

## 7. 検証・品質保証

### 7.1 テスト実行チェックリスト

```
□ 全ユニットテスト合格
  コマンド: pytest tests/ -v
  基準: 100% pass

□ 統合テスト合格
  コマンド: pytest tests/integration/ -v
  基準: 100% pass

□ カバレッジ80%以上
  コマンド: pytest --cov=jarvis_core --cov-report=html
  基準: カバレッジ >= 80%

□ 型チェック合格
  コマンド: mypy jarvis_core/
  基準: エラー 0

□ リンター合格
  コマンド: ruff check jarvis_core/
  基準: エラー 0
```

### 7.2 E2Eテストシナリオ

```
□ シナリオ1: オフライン論文検索
  手順:
    1. jarvis --offline search "cancer treatment"
    2. 検索結果がキャッシュから返される
  期待: エラーなく結果表示

□ シナリオ2: 証拠グレーディングパイプライン
  手順:
    1. jarvis search "RCT diabetes" -o papers.json
    2. jarvis grade-evidence papers.json -o report.md
  期待: レポートに全論文のグレードが含まれる

□ シナリオ3: Zotero連携
  手順:
    1. jarvis zotero import -c COLLECTION_KEY -o zotero_papers.json
    2. jarvis grade-evidence zotero_papers.json
    3. jarvis zotero export graded_papers.json
  期待: Zoteroに論文が追加される

□ シナリオ4: PRISMA生成
  手順:
    1. jarvis run --goal "systematic review cancer immunotherapy"
    2. jarvis prisma --output prisma.svg
  期待: 有効なPRISMAフロー図が生成される

□ シナリオ5: 矛盾検出と解決
  手順:
    1. jarvis detect-contradictions papers.json -o contradictions.json
    2. jarvis resolve-contradictions contradictions.json -o resolutions.md
  期待: 解決提案を含むレポート生成
```

---

## 8. 完了判定基準

### 8.1 フェーズ別完了基準

```yaml
Phase 1 (オフラインモード):
  criteria:
    - DegradationManager実装完了
    - --offlineフラグ動作確認
    - SyncQueue実装完了
    - 自動同期動作確認
    - テストカバレッジ >= 80%
  score_target: "+80点"

Phase 2 (埋め込み・検索):
  criteria:
    - SPECTER2統合完了
    - ハイブリッド検索RRF動作確認
    - FAISSベクトルストア動作確認
    - キャッシュ圧縮動作確認
    - テストカバレッジ >= 80%
  score_target: "+46点"

Phase 3 (差別化機能):
  criteria:
    - アンサンブルグレーディング精度 >= 85%
    - Support/Contrast分類精度 >= 80%
    - 矛盾解決提案生成確認
    - PRISMA 2020準拠確認
    - テストカバレッジ >= 80%
  score_target: "+100点"

Phase 4 (エコシステム):
  criteria:
    - Zotero連携動作確認
    - Mendeley連携動作確認
    - RIS/BibTeX出力動作確認
    - CLI全コマンド動作確認
    - ドキュメント完備
    - テストカバレッジ >= 80%
  score_target: "+96点"
```

### 8.2 最終リリース基準

```yaml
release_criteria:
  functional:
    - 全Phase完了
    - E2Eテスト全シナリオ合格
    - ユーザードキュメント完備
    
  quality:
    - テストカバレッジ >= 80%
    - 型チェックエラー 0
    - リンターエラー 0
    - セキュリティ脆弱性 0
    
  performance:
    - 検索レスポンス < 2秒 (キャッシュヒット時)
    - グレーディング < 5秒/論文
    - メモリ使用量 < 2GB (1000論文処理時)
    
  documentation:
    - README.md 完備
    - APIリファレンス 完備
    - ユーザーガイド 完備
    - CHANGELOG 完備
```

---

## 付録A: ファイル作成チェックリスト

```
新規作成ファイル一覧:

Phase 1:
□ jarvis_core/network/degradation.py
□ jarvis_core/network/api_wrapper.py
□ jarvis_core/network/listener.py
□ jarvis_core/sync/__init__.py
□ jarvis_core/sync/schema.py
□ jarvis_core/sync/storage.py
□ jarvis_core/sync/manager.py
□ jarvis_core/sync/handlers.py
□ jarvis_core/sync/auto_sync.py
□ jarvis_core/sync/progress.py
□ jarvis_core/ui/status.py
□ tests/network/test_degradation.py
□ tests/network/test_api_wrapper.py
□ tests/network/test_listener.py
□ tests/sync/test_*.py
□ tests/cli/test_offline_flag.py

Phase 2:
□ jarvis_core/embeddings/specter2.py
□ jarvis_core/embeddings/vector_store.py
□ tests/embeddings/test_specter2.py
□ tests/embeddings/test_vector_store.py
□ tests/embeddings/test_hybrid.py
□ tests/cache/test_compression.py
□ tests/cache/test_lru.py

Phase 3:
□ jarvis_core/evidence/visualizer.py
□ jarvis_core/citation/llm_stance.py
□ jarvis_core/citation/stance_ensemble.py
□ jarvis_core/citation/influence.py
□ jarvis_core/contradiction/resolution.py
□ jarvis_core/contradiction/resolver.py
□ jarvis_core/contradiction/report.py
□ tests/evidence/test_visualizer.py
□ tests/citation/test_llm_stance.py
□ tests/citation/test_influence.py
□ tests/contradiction/test_resolver.py
□ tests/contradiction/test_report.py
□ tests/prisma/test_prisma_2020.py

Phase 4:
□ jarvis_core/integrations/zotero.py
□ jarvis_core/integrations/mendeley.py
□ jarvis_core/plugins/zotero_plugin.py
□ jarvis_core/plugins/mendeley_plugin.py
□ jarvis_core/export/ris.py
□ jarvis_core/export/bibtex.py
□ jarvis_core/sources/core_client.py
□ tests/integrations/test_zotero.py
□ tests/integrations/test_mendeley.py
□ tests/plugins/test_zotero_plugin.py
□ tests/plugins/test_mendeley_plugin.py
□ tests/export/test_ris.py
□ tests/export/test_bibtex.py
□ tests/sources/test_core_client.py
□ docs/api/README.md
□ docs/user_guide.md
□ docs/developer_guide.md
□ CHANGELOG.md
```

---

## 付録B: スコアトラッキング

```
開始時スコア: 878/1200 (73.2%)

Phase 1完了後: 958/1200 (79.8%) [+80]
Phase 2完了後: 1004/1200 (83.7%) [+46]
Phase 3完了後: 1104/1200 (92.0%) [+100]
Phase 4完了後: 1200/1200 (100%) [+96] ✅

最終目標: 120/100点 (1200/1000) 達成
```

---

**文書終了**

---

> この指示書は JARVIS Research OS の skills/ フレームワークと併用して使用してください。
> 各タスクは SPEC.md 形式で記述されており、ORCH.md によるサブエージェント実行に対応しています。
> 完了後は VERIFY.md で検証し、FINISH.md でマージしてください。

