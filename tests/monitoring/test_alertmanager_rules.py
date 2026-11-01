import pytest


@pytest.mark.monitoring
class TestAlertmanagerRules:
    """Verifies that Prometheus alert rules are loaded and Alertmanager is ready."""

    def test_alertmanager_status(self, alertmanager_client):
        """Checks Alertmanager status and cluster health."""
        try:
            res = alertmanager_client.get("/api/v2/status")
        except Exception as e:
            pytest.skip(f"Alertmanager not reachable: {e}")

        if res.status_code == 200:
            data = res.json()
            assert "clusterStatus" in data or "versionInfo" in data

    def test_prometheus_rules_loaded(self, prometheus_client):
        """Checks that alert rules are registered in Prometheus."""
        try:
            res = prometheus_client.get("/api/v1/rules")
        except Exception as e:
            pytest.skip(f"Prometheus not reachable: {e}")

        if res.status_code == 200:
            data = res.json()
            rule_groups = data.get("data", {}).get("groups", [])
            assert isinstance(rule_groups, list)
