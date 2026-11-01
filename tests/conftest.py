import time
from uuid import uuid4

import httpx
import pytest

from config.settings import settings


@pytest.fixture(scope="session")
def env_settings():
    """Provides test environment configuration."""
    return settings


@pytest.fixture
def ingestion_client():
    """HTTP client for Ingestion API."""
    headers = {
        "Authorization": f"Bearer {settings.INGESTION_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    with httpx.Client(base_url=settings.INGESTION_BASE_URL, headers=headers, timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        yield client


@pytest.fixture
def business_client():
    """HTTP client for Business API."""
    headers = {
        "Authorization": f"Bearer {settings.BUSINESS_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    with httpx.Client(base_url=settings.BUSINESS_BASE_URL, headers=headers, timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        yield client


@pytest.fixture
def rag_client():
    """HTTP client for RAG Service."""
    headers = {
        "Content-Type": "application/json",
    }
    with httpx.Client(base_url=settings.RAG_BASE_URL, headers=headers, timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        yield client


@pytest.fixture
def prometheus_client():
    """HTTP client for Prometheus Server."""
    with httpx.Client(base_url=settings.PROMETHEUS_BASE_URL, timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        yield client


@pytest.fixture
def alertmanager_client():
    """HTTP client for Alertmanager."""
    with httpx.Client(base_url=settings.ALERTMANAGER_BASE_URL, timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        yield client


@pytest.fixture
def sample_sensor_reading():
    """Generates a valid sensor telemetry payload adhering to MaintAI Contracts v1.3 / v1.4."""
    def _generator(machine_id: str = "M-001", tool_wear_min: int = 108, high_risk: bool = False):
        seq = int(time.time() * 1000) % 1000000
        # If high_risk is True, set high torque and process temperature to trigger degradation
        torque = 78.5 if high_risk else 42.8
        temp = 320.0 if high_risk else 308.6
        return {
            "schema_version": "1.3.0",
            "event_id": f"evt_systest_{uuid4().hex[:12]}",
            "machine_id": machine_id,
            "stream_epoch": "systest-run",
            "sequence_number": seq,
            "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "SYSTEM_TEST_RUNNER",
            "features": {
                "product_type": "M",
                "air_temperature_k": 298.1,
                "process_temperature_k": temp,
                "rotational_speed_rpm": 1551,
                "torque_nm": torque,
                "tool_wear_min": tool_wear_min,
            },
            "correlation_id": f"cor_systest_{uuid4().hex[:12]}",
        }
    return _generator
