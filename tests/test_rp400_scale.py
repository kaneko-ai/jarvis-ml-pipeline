"""Tests for RP-400+ scale/security features.

Core tests for scale and security.
"""
import pytest

pytestmark = pytest.mark.core


class TestDistributed:
    """Tests for RP-400 Distributed Processing."""

    def test_local_execution(self):
        """Should execute locally."""
        from jarvis_core.runtime.distributed import DistributedProcessor

        dp = DistributedProcessor(backend="local")
        dp.initialize()

        def add(x):
            return x + 1

        task_id = dp.submit(add, 5)
        result = dp.get_result(task_id)

        assert result == 6

    def test_map(self):
        """Should map over items."""
        from jarvis_core.runtime.distributed import DistributedProcessor

        dp = DistributedProcessor(backend="local")
        dp.initialize()

        results = dp.map(lambda x: x * 2, [1, 2, 3])

        assert results == [2, 4, 6]


class TestRBAC:
    """Tests for RP-418 RBAC."""

    def test_default_roles(self):
        """Default roles should exist."""
        from jarvis_core.security.rbac import RBAC

        rbac = RBAC()

        admin = rbac.get_role("admin")
        assert admin is not None

    def test_user_permissions(self):
        """Should aggregate user permissions."""
        from jarvis_core.security.rbac import RBAC, Permission

        rbac = RBAC()
        rbac.create_user("u1", "user1", ["researcher"])

        perms = rbac.get_user_permissions("u1")

        assert Permission.RUN_QUERY in perms
        assert Permission.MANAGE_USERS not in perms

    def test_check_permission(self):
        """Should check permissions."""
        from jarvis_core.security.rbac import RBAC, Permission

        rbac = RBAC()
        rbac.create_user("u1", "user1", ["viewer"])

        assert rbac.check_permission("u1", Permission.READ)
        assert not rbac.check_permission("u1", Permission.DELETE)


class TestPluginManager:
    """Tests for RP-425 Plugin Architecture."""

    def test_list_active(self):
        """Should list active plugins."""
        from jarvis_core.plugins import PluginManager

        pm = PluginManager()
        active = pm.list_active_plugins()

        assert isinstance(active, list)
