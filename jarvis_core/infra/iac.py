"""Infrastructure as Code Module.

Per RP-596, implements Terraform-like IaC management.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ResourceState(Enum):
    """Resource states."""

    PENDING = "pending"
    CREATING = "creating"
    CREATED = "created"
    UPDATING = "updating"
    DELETING = "deleting"
    DELETED = "deleted"
    FAILED = "failed"


@dataclass
class Resource:
    """An infrastructure resource."""

    resource_id: str
    resource_type: str
    name: str
    properties: dict[str, Any]
    state: ResourceState = ResourceState.PENDING
    outputs: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Plan:
    """An execution plan."""

    to_create: list[Resource]
    to_update: list[Resource]
    to_delete: list[Resource]
    no_change: list[Resource]


class StateManager:
    """Manages infrastructure state.

    Per RP-596:
    - State persistence
    - Drift detection
    - Locking
    """

    def __init__(self, state_path: str = "infra/state.json"):
        self.state_path = Path(state_path)
        self._state: dict[str, Resource] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        if self.state_path.exists():
            with open(self.state_path) as f:
                data = json.load(f)
                for res_id, res_data in data.get("resources", {}).items():
                    self._state[res_id] = Resource(
                        resource_id=res_id,
                        resource_type=res_data["type"],
                        name=res_data["name"],
                        properties=res_data["properties"],
                        state=ResourceState(res_data["state"]),
                        outputs=res_data.get("outputs", {}),
                    )

    def _save_state(self) -> None:
        """Save state to file."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "resources": {
                res_id: {
                    "type": res.resource_type,
                    "name": res.name,
                    "properties": res.properties,
                    "state": res.state.value,
                    "outputs": res.outputs,
                }
                for res_id, res in self._state.items()
            }
        }

        with open(self.state_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_resource(self, resource_id: str) -> Resource | None:
        """Get resource by ID."""
        return self._state.get(resource_id)

    def set_resource(self, resource: Resource) -> None:
        """Set resource in state."""
        self._state[resource.resource_id] = resource
        self._save_state()

    def delete_resource(self, resource_id: str) -> None:
        """Delete resource from state."""
        if resource_id in self._state:
            del self._state[resource_id]
            self._save_state()

    def list_resources(self) -> list[Resource]:
        """List all resources."""
        return list(self._state.values())


class InfrastructureManager:
    """Manages infrastructure as code.

    Per RP-596:
    - Terraform-like workflow
    - Plan and apply
    - Drift detection
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
    ):
        self.state = state_manager or StateManager()
        self._providers: dict[str, Any] = {}

    def register_provider(
        self,
        resource_type: str,
        provider: Any,
    ) -> None:
        """Register a resource provider.

        Args:
            resource_type: Resource type.
            provider: Provider instance.
        """
        self._providers[resource_type] = provider

    def plan(
        self,
        desired: list[Resource],
    ) -> Plan:
        """Create an execution plan.

        Args:
            desired: Desired resources.

        Returns:
            Execution plan.
        """
        current = {r.resource_id: r for r in self.state.list_resources()}
        desired_map = {r.resource_id: r for r in desired}

        to_create = []
        to_update = []
        to_delete = []
        no_change = []

        # Check for creates and updates
        for res_id, res in desired_map.items():
            if res_id not in current:
                to_create.append(res)
            elif res.properties != current[res_id].properties:
                to_update.append(res)
            else:
                no_change.append(res)

        # Check for deletes
        for res_id in current:
            if res_id not in desired_map:
                to_delete.append(current[res_id])

        return Plan(
            to_create=to_create,
            to_update=to_update,
            to_delete=to_delete,
            no_change=no_change,
        )

    def apply(self, plan: Plan) -> dict[str, Any]:
        """Apply an execution plan.

        Args:
            plan: Execution plan.

        Returns:
            Apply results.
        """
        results = {
            "created": [],
            "updated": [],
            "deleted": [],
            "errors": [],
        }

        # Create resources
        for res in plan.to_create:
            try:
                res.state = ResourceState.CREATING
                self.state.set_resource(res)

                provider = self._providers.get(res.resource_type)
                if provider:
                    outputs = provider.create(res)
                    res.outputs = outputs or {}

                res.state = ResourceState.CREATED
                self.state.set_resource(res)
                results["created"].append(res.resource_id)
            except Exception as e:
                res.state = ResourceState.FAILED
                self.state.set_resource(res)
                results["errors"].append(
                    {
                        "resource": res.resource_id,
                        "error": str(e),
                    }
                )

        # Update resources
        for res in plan.to_update:
            try:
                res.state = ResourceState.UPDATING
                self.state.set_resource(res)

                provider = self._providers.get(res.resource_type)
                if provider:
                    outputs = provider.update(res)
                    res.outputs = outputs or {}

                res.state = ResourceState.CREATED
                self.state.set_resource(res)
                results["updated"].append(res.resource_id)
            except Exception as e:
                res.state = ResourceState.FAILED
                self.state.set_resource(res)
                results["errors"].append(
                    {
                        "resource": res.resource_id,
                        "error": str(e),
                    }
                )

        # Delete resources
        for res in plan.to_delete:
            try:
                res.state = ResourceState.DELETING
                self.state.set_resource(res)

                provider = self._providers.get(res.resource_type)
                if provider:
                    provider.delete(res)

                self.state.delete_resource(res.resource_id)
                results["deleted"].append(res.resource_id)
            except Exception as e:
                res.state = ResourceState.FAILED
                self.state.set_resource(res)
                results["errors"].append(
                    {
                        "resource": res.resource_id,
                        "error": str(e),
                    }
                )

        return results

    def detect_drift(self) -> list[dict[str, Any]]:
        """Detect configuration drift.

        Returns:
            List of drifted resources.
        """
        drifts = []

        for res in self.state.list_resources():
            provider = self._providers.get(res.resource_type)
            if provider and hasattr(provider, "get_current"):
                try:
                    current = provider.get_current(res)
                    if current != res.properties:
                        drifts.append(
                            {
                                "resource_id": res.resource_id,
                                "expected": res.properties,
                                "actual": current,
                            }
                        )
                except Exception as e:
                    logger.debug(f"Failed to detect drift for {res.resource_id}: {e}")

        return drifts
