import pytest


@pytest.mark.e2e
class TestSensorIngestionE2E:
    """End-to-End tests for sensor readings ingestion pipeline."""

    def test_ingestion_health_endpoints(self, ingestion_client):
        """Verifies Ingestion API liveness and readiness."""
        live_res = ingestion_client.get("/health/live")
        assert live_res.status_code == 200, f"Liveness probe failed: {live_res.text}"
        assert live_res.json().get("status") == "UP"

        ready_res = ingestion_client.get("/health/ready")
        assert ready_res.status_code in (200, 503), f"Readiness probe error: {ready_res.text}"

    def test_post_valid_telemetry_accepted(self, ingestion_client, sample_sensor_reading):
        """Verifies valid telemetry gets HTTP 202 Accepted and proper correlation headers."""
        payload = sample_sensor_reading(machine_id="M-001", tool_wear_min=50, high_risk=False)

        response = ingestion_client.post("/api/v1/sensor-readings", json=payload)
        assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"

        body = response.json()
        assert body.get("status") in ("ACCEPTED", "PROCESSED", "OK", None) or "ack" in str(body).lower()

        # Contract requirement: X-Request-ID and X-Correlation-ID headers must be present
        assert "x-request-id" in response.headers or "X-Request-ID" in response.headers
        assert "x-correlation-id" in response.headers or "X-Correlation-ID" in response.headers

    def test_post_malformed_telemetry_rejected(self, ingestion_client):
        """Verifies malformed or incomplete telemetry is safely rejected with 400 or 422."""
        invalid_payload = {
            "schema_version": "1.3.0",
            # Missing machine_id, features, etc.
            "event_id": "malformed_evt",
        }

        response = ingestion_client.post("/api/v1/sensor-readings", json=invalid_payload)
        assert response.status_code in (400, 422), (
            f"Expected rejection (400 or 422), but got {response.status_code}: {response.text}"
        )
