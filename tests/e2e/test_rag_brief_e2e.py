import pytest


@pytest.mark.e2e
class TestRAGBriefE2E:
    """End-to-End tests for RAG Copilot maintenance brief generation."""

    def test_rag_health(self, rag_client):
        """Verifies RAG service health endpoint."""
        res = rag_client.get("/health/live")
        assert res.status_code == 200, f"RAG liveness failed: {res.text}"
        assert res.json().get("status") == "UP"

    def test_generate_maintenance_brief(self, rag_client):
        """Verifies requesting a maintenance brief with alert context."""
        payload = {
            "intent": "MAINTENANCE_BRIEF",
            "alert": {
                "alert_id": "alt_systest_001",
                "machine_id": "M-001",
                "severity": "CRITICAL",
                "status": "OPEN",
                "risk_score": 0.88,
                "policy_version": "v1.0.0",
            },
            "prediction": {
                "prediction_id": "pred_systest_001",
                "prediction": "FAILURE_RISK_HIGH",
                "failure_probability": 0.88,
                "model_version": "v1.0.0",
            },
            "sensor_context": {
                "product_type": "M",
                "air_temperature_k": 298.1,
                "process_temperature_k": 320.0,
                "rotational_speed_rpm": 1551.0,
                "torque_nm": 78.5,
                "tool_wear_min": 108.0,
            },
        }

        res = rag_client.post("/api/v1/briefs", json=payload)
        # RAG may return 200 (if Groq / LLM key is configured) or 503 RAG_UNAVAILABLE (if provider key is not set)
        assert res.status_code in (200, 503), f"Unexpected status: {res.status_code}: {res.text}"

        if res.status_code == 200:
            data = res.json()
            assert "summary" in data or "brief" in data
            assert "grounded_status" in data
            assert isinstance(data.get("checklist", []), list)
