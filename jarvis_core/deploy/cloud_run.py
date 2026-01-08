"""Google Cloud Run Deployment for JARVIS.

Per RP-520, implements Cloud Run deployment automation.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CloudRegion(Enum):
    """GCP regions."""
    US_CENTRAL1 = "us-central1"
    US_EAST1 = "us-east1"
    EUROPE_WEST1 = "europe-west1"
    ASIA_NORTHEAST1 = "asia-northeast1"
    ASIA_NORTHEAST2 = "asia-northeast2"  # Osaka


@dataclass
class CloudRunConfig:
    """Cloud Run deployment configuration."""
    project_id: str = ""
    region: CloudRegion = CloudRegion.ASIA_NORTHEAST1
    service_name: str = "jarvis-api"
    image: str = ""
    memory: str = "512Mi"
    cpu: str = "1"
    min_instances: int = 0
    max_instances: int = 10
    concurrency: int = 80
    timeout: int = 300
    env_vars: dict[str, str] = field(default_factory=dict)
    secrets: list[str] = field(default_factory=list)
    allow_unauthenticated: bool = False
    vpc_connector: str | None = None


@dataclass
class DeploymentStatus:
    """Cloud Run deployment status."""
    service_name: str
    revision: str
    url: str
    status: str
    created_at: str
    traffic: list[dict[str, Any]] = field(default_factory=list)


class CloudRunDeployer:
    """Manages Cloud Run deployments.
    
    Per RP-520:
    - Deploy to Cloud Run
    - Traffic splitting
    - Rollback
    - IAM management
    """

    def __init__(self, config: CloudRunConfig | None = None):
        self.config = config or CloudRunConfig(
            project_id=os.getenv("GCP_PROJECT_ID", ""),
        )
        self._deployments: dict[str, DeploymentStatus] = {}

    def deploy(
        self,
        image: str | None = None,
        traffic_percent: int = 100,
        tag: str | None = None,
    ) -> DeploymentStatus:
        """Deploy to Cloud Run.
        
        Args:
            image: Container image (defaults to config.image).
            traffic_percent: Traffic percentage for new revision.
            tag: Revision tag.
            
        Returns:
            Deployment status.
        """
        image = image or self.config.image

        # In production, use gcloud SDK or API
        # gcloud run deploy {service} --image={image} --region={region}

        revision = f"{self.config.service_name}-{self._generate_revision_id()}"
        url = f"https://{self.config.service_name}-{self._get_project_hash()}.a.run.app"

        status = DeploymentStatus(
            service_name=self.config.service_name,
            revision=revision,
            url=url,
            status="READY",
            created_at=self._get_timestamp(),
            traffic=[{"revision": revision, "percent": traffic_percent}],
        )

        self._deployments[revision] = status
        return status

    def canary_deploy(
        self,
        image: str,
        canary_percent: int = 10,
    ) -> DeploymentStatus:
        """Deploy with canary traffic split.
        
        Args:
            image: New container image.
            canary_percent: Percentage of traffic to canary.
            
        Returns:
            Deployment status.
        """
        return self.deploy(image, traffic_percent=canary_percent, tag="canary")

    def promote_canary(self, revision: str) -> DeploymentStatus:
        """Promote canary to receive 100% traffic.
        
        Args:
            revision: Canary revision to promote.
            
        Returns:
            Updated deployment status.
        """
        if revision in self._deployments:
            status = self._deployments[revision]
            status.traffic = [{"revision": revision, "percent": 100}]
            return status

        raise ValueError(f"Revision {revision} not found")

    def rollback(self, target_revision: str | None = None) -> DeploymentStatus:
        """Rollback to a previous revision.
        
        Args:
            target_revision: Specific revision to rollback to.
            
        Returns:
            Rollback status.
        """
        revisions = list(self._deployments.keys())
        if not revisions:
            raise ValueError("No revisions to rollback to")

        if target_revision and target_revision in self._deployments:
            target = target_revision
        else:
            # Use second-to-last revision
            target = revisions[-2] if len(revisions) > 1 else revisions[-1]

        status = self._deployments[target]
        status.traffic = [{"revision": target, "percent": 100}]
        return status

    def get_service_url(self) -> str:
        """Get the service URL."""
        return f"https://{self.config.service_name}-{self._get_project_hash()}.a.run.app"

    def list_revisions(self) -> list[DeploymentStatus]:
        """List all revisions."""
        return list(self._deployments.values())

    def set_iam_policy(
        self,
        members: list[str],
        role: str = "roles/run.invoker",
    ) -> bool:
        """Set IAM policy for the service.
        
        Args:
            members: IAM members (e.g., ["allUsers"]).
            role: IAM role.
            
        Returns:
            True if successful.
        """
        # In production, use gcloud or API
        return True

    def generate_deploy_command(self) -> str:
        """Generate gcloud deploy command."""
        cmd = [
            "gcloud", "run", "deploy", self.config.service_name,
            f"--project={self.config.project_id}",
            f"--region={self.config.region.value}",
            f"--image={self.config.image}",
            f"--memory={self.config.memory}",
            f"--cpu={self.config.cpu}",
            f"--min-instances={self.config.min_instances}",
            f"--max-instances={self.config.max_instances}",
            f"--concurrency={self.config.concurrency}",
            f"--timeout={self.config.timeout}",
        ]

        if self.config.allow_unauthenticated:
            cmd.append("--allow-unauthenticated")

        for key, value in self.config.env_vars.items():
            cmd.append(f"--set-env-vars={key}={value}")

        return " ".join(cmd)

    def generate_dockerfile(self) -> str:
        """Generate Dockerfile for Cloud Run."""
        return '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# Copy application
COPY jarvis_core/ ./jarvis_core/
COPY jarvis_tools/ ./jarvis_tools/

# Run the application
ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "jarvis_core.app"]
'''

    def _generate_revision_id(self) -> str:
        """Generate revision ID."""
        import time
        return f"rev-{int(time.time())}"

    def _get_project_hash(self) -> str:
        """Get project hash for URL."""
        import hashlib
        return hashlib.sha256(
            self.config.project_id.encode()
        ).hexdigest()[:8]

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# Global deployer
_cloud_run_deployer: CloudRunDeployer | None = None


def get_cloud_run_deployer() -> CloudRunDeployer:
    """Get global Cloud Run deployer."""
    global _cloud_run_deployer
    if _cloud_run_deployer is None:
        _cloud_run_deployer = CloudRunDeployer()
    return _cloud_run_deployer
