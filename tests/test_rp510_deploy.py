"""Tests for RP-510, RP-535, RP-581 implementations."""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.core


class TestCanaryDeployment:
    """Tests for Canary Deployment (RP-510)."""

    def test_manager_init(self):
        """Test manager initialization."""
        from jarvis_core.deploy.canary import CanaryDeploymentManager

        manager = CanaryDeploymentManager()
        assert manager is not None

    def test_deploy_canary(self):
        """Test canary deployment."""
        from jarvis_core.deploy.canary import CanaryDeploymentManager

        manager = CanaryDeploymentManager()
        result = manager.deploy_canary(
            new_version="v1.1.0",
            new_image="jarvis:v1.1.0",
            current_version="v1.0.0",
        )

        assert result.success
        assert result.new_version == "v1.1.0"
        assert result.old_version == "v1.0.0"
        assert result.strategy.value == "canary"

    def test_deploy_blue_green(self):
        """Test blue-green deployment."""
        from jarvis_core.deploy.canary import CanaryDeploymentManager

        manager = CanaryDeploymentManager()
        # First set up a current version
        manager.deploy_canary("v1.0.0", "jarvis:v1.0.0")

        result = manager.deploy_blue_green(
            new_version="v2.0.0",
            new_image="jarvis:v2.0.0",
        )

        assert result.success
        assert result.strategy.value == "blue_green"

    def test_get_current_version(self):
        """Test getting current version."""
        from jarvis_core.deploy.canary import CanaryDeploymentManager

        manager = CanaryDeploymentManager()
        manager.deploy_canary("v1.0.0", "jarvis:v1.0.0")

        assert manager.get_current_version() == "v1.0.0"

    def test_deployment_history(self):
        """Test deployment history."""
        from jarvis_core.deploy.canary import CanaryDeploymentManager

        manager = CanaryDeploymentManager()
        manager.deploy_canary("v1.0.0", "jarvis:v1.0.0")
        manager.deploy_canary("v1.1.0", "jarvis:v1.1.0")

        history = manager.get_deployment_history()
        assert len(history) == 2


class TestSentryErrorTracking:
    """Tests for Sentry Error Tracking (RP-535)."""

    def test_client_init(self):
        """Test Sentry client initialization."""
        from jarvis_core.monitoring.sentry import SentryClient

        client = SentryClient()
        assert client is not None

    def test_capture_exception(self):
        """Test capturing an exception."""
        from jarvis_core.monitoring.sentry import SentryClient, SentryConfig

        config = SentryConfig(dsn="test-dsn")
        client = SentryClient(config)

        try:
            raise ValueError("Test error")
        except ValueError:
            event_id = client.capture_exception()
            assert event_id is not None

    def test_capture_message(self):
        """Test capturing a message."""
        from jarvis_core.monitoring.sentry import ErrorLevel, SentryClient, SentryConfig

        config = SentryConfig(dsn="test-dsn")
        client = SentryClient(config)

        event_id = client.capture_message("Test message", level=ErrorLevel.WARNING)
        assert event_id is not None

    def test_breadcrumbs(self):
        """Test adding breadcrumbs."""
        from jarvis_core.monitoring.sentry import SentryClient

        client = SentryClient()
        client.add_breadcrumb("http", "Request to /api", data={"url": "/api"})

        assert len(client._breadcrumbs) == 1

    def test_set_user(self):
        """Test setting user context."""
        from jarvis_core.monitoring.sentry import SentryClient

        client = SentryClient()
        client.set_user(user_id="user-123", username="test_user")

        assert client._user["id"] == "user-123"

    def test_set_tags(self):
        """Test setting tags."""
        from jarvis_core.monitoring.sentry import SentryClient

        client = SentryClient()
        client.set_tag("environment", "test")

        assert client._tags["environment"] == "test"

    def test_error_levels(self):
        """Test error level enum."""
        from jarvis_core.monitoring.sentry import ErrorLevel

        assert ErrorLevel.DEBUG.value == "debug"
        assert ErrorLevel.INFO.value == "info"
        assert ErrorLevel.ERROR.value == "error"
        assert ErrorLevel.FATAL.value == "fatal"


class TestDisasterRecovery:
    """Tests for Disaster Recovery (RP-581)."""

    def test_manager_init(self):
        """Test DR manager initialization."""
        from jarvis_core.reliability.disaster_recovery import DisasterRecoveryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            from jarvis_core.reliability.disaster_recovery import BackupConfig

            config = BackupConfig(backup_dir=tmpdir)
            manager = DisasterRecoveryManager(config)
            assert manager is not None

    def test_create_backup(self):
        """Test creating a backup."""
        from jarvis_core.reliability.disaster_recovery import BackupConfig, DisasterRecoveryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source files
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "test.txt").write_text("test content")

            backup_dir = Path(tmpdir) / "backups"
            config = BackupConfig(backup_dir=str(backup_dir))
            manager = DisasterRecoveryManager(config)

            metadata = manager.create_backup([str(source_dir)])

            assert metadata.backup_id is not None
            assert metadata.files_count >= 1

    def test_list_backups(self):
        """Test listing backups."""
        from jarvis_core.reliability.disaster_recovery import BackupConfig, DisasterRecoveryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "test.txt"
            source_file.write_text("test")

            backup_dir = Path(tmpdir) / "backups"
            config = BackupConfig(backup_dir=str(backup_dir))
            manager = DisasterRecoveryManager(config)

            manager.create_backup([str(source_file)])
            manager.create_backup([str(source_file)])

            backups = manager.list_backups()
            assert len(backups) == 2

    def test_restore_backup(self):
        """Test restoring from backup."""
        from jarvis_core.reliability.disaster_recovery import BackupConfig, DisasterRecoveryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "test.txt"
            source_file.write_text("original content")

            backup_dir = Path(tmpdir) / "backups"
            restore_dir = Path(tmpdir) / "restored"
            restore_dir.mkdir()

            config = BackupConfig(backup_dir=str(backup_dir), compression=False)
            manager = DisasterRecoveryManager(config)

            metadata = manager.create_backup([str(source_file)])
            result = manager.restore_backup(metadata.backup_id, str(restore_dir))

            assert result.success
            assert result.restored_files >= 1

    def test_verify_backup(self):
        """Test verifying backup integrity."""
        from jarvis_core.reliability.disaster_recovery import BackupConfig, DisasterRecoveryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "test.txt"
            source_file.write_text("test")

            backup_dir = Path(tmpdir) / "backups"
            config = BackupConfig(backup_dir=str(backup_dir), compression=False)
            manager = DisasterRecoveryManager(config)

            metadata = manager.create_backup([str(source_file)])
            is_valid = manager.verify_backup(metadata.backup_id)

            assert is_valid

    def test_delete_backup(self):
        """Test deleting a backup."""
        from jarvis_core.reliability.disaster_recovery import BackupConfig, DisasterRecoveryManager

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "test.txt"
            source_file.write_text("test")

            backup_dir = Path(tmpdir) / "backups"
            config = BackupConfig(backup_dir=str(backup_dir))
            manager = DisasterRecoveryManager(config)

            metadata = manager.create_backup([str(source_file)])
            deleted = manager.delete_backup(metadata.backup_id)

            assert deleted
            assert len(manager.list_backups()) == 0


class TestDeploymentStrategies:
    """Additional tests for deployment strategies."""

    def test_deployment_strategy_enum(self):
        """Test deployment strategy enum."""
        from jarvis_core.deploy.canary import DeploymentStrategy

        assert DeploymentStrategy.ROLLING.value == "rolling"
        assert DeploymentStrategy.CANARY.value == "canary"
        assert DeploymentStrategy.BLUE_GREEN.value == "blue_green"

    def test_canary_config(self):
        """Test canary configuration."""
        from jarvis_core.deploy.canary import CanaryConfig

        config = CanaryConfig(
            initial_weight=0.05,
            increment=0.05,
            success_threshold=0.999,
        )

        assert config.initial_weight == 0.05
        assert config.success_threshold == 0.999

    def test_deployment_version(self):
        """Test deployment version dataclass."""
        from jarvis_core.deploy.canary import DeploymentVersion

        version = DeploymentVersion(
            version="v1.0.0",
            image="jarvis:v1.0.0",
            replicas=3,
        )

        assert version.version == "v1.0.0"
        assert version.replicas == 3
        assert version.healthy is True


class TestBackupTypes:
    """Tests for backup type configurations."""

    def test_backup_type_enum(self):
        """Test backup type enum."""
        from jarvis_core.reliability.disaster_recovery import BackupType

        assert BackupType.FULL.value == "full"
        assert BackupType.INCREMENTAL.value == "incremental"

    def test_rpo_rto_enums(self):
        """Test RPO/RTO enums."""
        from jarvis_core.reliability.disaster_recovery import (
            RecoveryPointObjective,
            RecoveryTimeObjective,
        )

        assert RecoveryPointObjective.MINUTES_1.value == 60
        assert RecoveryTimeObjective.MINUTES_5.value == 300