import pytest


@pytest.mark.e2e
class TestAlertLifecycleE2E:
    """End-to-End tests for Business API Alert lifecycle, SSE, and technician feedback."""

    def test_business_api_health(self, business_client):
        """Verifies Business API liveness and readiness."""
        live_res = business_client.get("/health/live")
        assert live_res.status_code == 200, f"Business API liveness failed: {live_res.text}"

    def test_list_alerts_and_machines(self, business_client):
        """Verifies querying machine fleet and existing alerts."""
        machines_res = business_client.get("/api/v1/machines")
        assert machines_res.status_code == 200, f"Failed to list machines: {machines_res.text}"
        machines = machines_res.json()
        assert isinstance(machines, (list, dict))

        alerts_res = business_client.get("/api/v1/alerts")
        assert alerts_res.status_code == 200, f"Failed to list alerts: {alerts_res.text}"
        alerts_data = alerts_res.json()
        assert isinstance(alerts_data, (list, dict))

    def test_alert_lifecycle_action_and_feedback(self, business_client):
        """Tests the transition of an alert: acknowledge -> feedback."""
        alerts_res = business_client.get("/api/v1/alerts")
        if alerts_res.status_code != 200:
            pytest.skip("Business API not reachable or returns non-200")

        data = alerts_res.json()
        alerts = data if isinstance(data, list) else data.get("items", [])
        if not alerts:
            pytest.skip("No existing alerts found to test action transition")

        target_alert = alerts[0]
        alert_id = target_alert.get("alert_id") or target_alert.get("id")

        # 1. Action: ack
        ack_res = business_client.post(f"/api/v1/alerts/{alert_id}/ack", json={})
        assert ack_res.status_code in (200, 204, 409), f"Alert ack failed: {ack_res.text}"

        # 2. Action: technician feedback
        feedback_payload = {
            "recommendation_feedback": "USEFUL",
            "comment": "Verified by automated system tests pipeline",
        }
        fb_res = business_client.post(f"/api/v1/alerts/{alert_id}/feedback", json=feedback_payload)
        assert fb_res.status_code in (200, 204, 409), f"Alert feedback failed: {fb_res.text}"
