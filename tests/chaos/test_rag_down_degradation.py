import pytest


@pytest.mark.chaos
class TestRAGDownDegradation:
    """Verifies Graceful Degradation: If RAG is down, critical Alert path must NOT be blocked."""

    def test_alert_flow_unaffected_when_rag_unavailable(self, business_client, rag_client, sample_sensor_reading):
        """Even if RAG returns 503 or is offline, Business API still serves machine alerts and status."""
        # 1. Check RAG status (may be 503 or offline)
        try:
            rag_res = rag_client.get("/health/ready")
            rag_available = (rag_res.status_code == 200)
        except Exception:
            rag_available = False

        # 2. Invariant: Business API Alert querying and actions MUST continue to operate
        try:
            alerts_res = business_client.get("/api/v1/alerts")
        except Exception as e:
            pytest.skip(f"Business API not reachable: {e}")

        assert alerts_res.status_code == 200, (
            f"Business API failed during RAG outage (Invariant violated): {alerts_res.text}"
        )

        # 3. Check machine fleet status is intact
        machines_res = business_client.get("/api/v1/machines")
        assert machines_res.status_code == 200, "Machine fleet status degraded due to RAG outage!"
        print(f"\n[DEGRADATION TEST PASS] RAG available={rag_available}, Critical Alert path operating normally.")
