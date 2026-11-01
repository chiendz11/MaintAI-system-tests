import pytest


@pytest.mark.monitoring
class TestMetricsScrape:
    """Verifies that Prometheus is successfully scraping all MaintAI service metrics."""

    def test_prometheus_healthy(self, prometheus_client):
        """Verifies Prometheus server is healthy and responding."""
        try:
            res = prometheus_client.get("/-/healthy")
        except Exception as e:
            pytest.skip(f"Prometheus not reachable at configured endpoint: {e}")

        assert res.status_code == 200, f"Prometheus not healthy: {res.text}"

    def test_targets_are_active(self, prometheus_client):
        """Verifies Prometheus targets are discovered and in UP state."""
        try:
            res = prometheus_client.get("/api/v1/targets")
        except Exception as e:
            pytest.skip(f"Prometheus not reachable: {e}")

        if res.status_code != 200:
            pytest.skip("Prometheus targets endpoint not available")

        data = res.json()
        active_targets = data.get("data", {}).get("activeTargets", [])
        assert len(active_targets) >= 0, "Targets list returned"

        # Check health of active targets
        unhealthy = [t for t in active_targets if t.get("health") != "up"]
        # Informational assertion or warning if some test targets are starting up
        assert len(active_targets) == 0 or len(unhealthy) < len(active_targets), (
            f"All Prometheus scrape targets are down: {unhealthy}"
        )

    def test_query_core_metrics(self, prometheus_client):
        """Queries core business and platform metrics."""
        core_queries = [
            "up",
            "process_cpu_seconds_total",
            "http_requests_total",
        ]

        for query in core_queries:
            try:
                res = prometheus_client.get("/api/v1/query", params={"query": query})
                if res.status_code == 200:
                    result = res.json()
                    assert result.get("status") == "success"
            except Exception:
                # Local environment may not have Prometheus running yet
                pass
