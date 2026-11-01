import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class TestEnvironmentSettings(BaseSettings):
        """Configuration settings for MaintAI system tests."""

        model_config = SettingsConfigDict(
            env_file=ROOT_DIR / "config" / "local-k3d.env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        # Environment
        ENVIRONMENT: str = Field(default="local-k3d", description="Target environment (local-k3d or staging)")
        NAMESPACE: str = Field(default="maintai-apps", description="Kubernetes namespace where apps run")

        # Ingestion API
        INGESTION_BASE_URL: str = Field(default="http://localhost:8001", description="Ingestion API base URL")
        INGESTION_AUTH_TOKEN: str = Field(default="mock-technician-token", description="Bearer token for Ingestion API")

        # Business API
        BUSINESS_BASE_URL: str = Field(default="http://localhost:8003", description="Business API base URL")
        BUSINESS_AUTH_TOKEN: str = Field(default="mock-technician-token", description="Bearer token for Business API")

        # RAG Service
        RAG_BASE_URL: str = Field(default="http://localhost:8005", description="RAG Service base URL")

        # ML Service
        ML_BASE_URL: str = Field(default="http://localhost:8002", description="ML Inference Service base URL")

        # Monitoring (Prometheus & Alertmanager)
        PROMETHEUS_BASE_URL: str = Field(default="http://localhost:9090", description="Prometheus server base URL")
        ALERTMANAGER_BASE_URL: str = Field(default="http://localhost:9093", description="Alertmanager base URL")

        # Kubernetes Cluster
        KUBECONFIG_PATH: str = Field(default="", description="Path to kubeconfig")

        # Timeouts
        REQUEST_TIMEOUT_SECONDS: float = Field(default=10.0, description="Default HTTP request timeout")
        RECOVERY_MAX_WAIT_SECONDS: int = Field(default=45, description="Max seconds to wait for pod recovery")

    settings = TestEnvironmentSettings()

except ImportError:
    class MinimalSettings:
        """Fallback settings when pydantic-settings is not installed."""
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local-k3d")
        NAMESPACE: str = os.getenv("NAMESPACE", "maintai-apps")
        INGESTION_BASE_URL: str = os.getenv("INGESTION_BASE_URL", "http://localhost:8001")
        INGESTION_AUTH_TOKEN: str = os.getenv("INGESTION_AUTH_TOKEN", "mock-technician-token")
        BUSINESS_BASE_URL: str = os.getenv("BUSINESS_BASE_URL", "http://localhost:8003")
        BUSINESS_AUTH_TOKEN: str = os.getenv("BUSINESS_AUTH_TOKEN", "mock-technician-token")
        RAG_BASE_URL: str = os.getenv("RAG_BASE_URL", "http://localhost:8005")
        ML_BASE_URL: str = os.getenv("ML_BASE_URL", "http://localhost:8002")
        PROMETHEUS_BASE_URL: str = os.getenv("PROMETHEUS_BASE_URL", "http://localhost:9090")
        ALERTMANAGER_BASE_URL: str = os.getenv("ALERTMANAGER_BASE_URL", "http://localhost:9093")
        KUBECONFIG_PATH: str = os.getenv("KUBECONFIG_PATH", "")
        REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10.0"))
        RECOVERY_MAX_WAIT_SECONDS: int = int(os.getenv("RECOVERY_MAX_WAIT_SECONDS", "45"))

    settings = MinimalSettings()
