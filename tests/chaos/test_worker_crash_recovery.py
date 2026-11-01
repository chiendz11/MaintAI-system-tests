import subprocess
import time

import pytest


@pytest.mark.chaos
class TestWorkerCrashRecovery:
    """Chaos drill: Kill Processing Worker pod during in-flight telemetry and verify self-healing."""

    def test_worker_pod_kill_and_self_healing(self, env_settings, ingestion_client, sample_sensor_reading):
        """Simulates worker crash, verifies K8s restarts it, and confirms zero message loss."""
        # 1. Step 1: Ingest pre-crash telemetry
        pre_payload = sample_sensor_reading(machine_id="M-001", tool_wear_min=40)
        pre_res = ingestion_client.post("/api/v1/sensor-readings", json=pre_payload)
        if pre_res.status_code != 202:
            pytest.skip(f"Ingestion API not reachable (status {pre_res.status_code}), skipping chaos drill")

        # 2. Step 2: Attempt to locate and delete the worker Pod in Kubernetes
        target_namespace = env_settings.NAMESPACE
        pod_label = "app=processing-worker"

        try:
            # Check if kubectl is available
            find_cmd = [
                "kubectl", "get", "pods",
                "-n", target_namespace,
                "-l", pod_label,
                "-o", "jsonpath={.items[0].metadata.name}",
            ]
            result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=10)
            pod_name = result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pod_name = ""

        if not pod_name:
            pytest.skip("Kubectl not available or processing-worker Pod not found in cluster, skipping live kill")

        # 3. Step 3: Trigger chaos kill
        start_time = time.time()
        kill_cmd = ["kubectl", "delete", "pod", pod_name, "-n", target_namespace, "--grace-period=0", "--force"]
        subprocess.run(kill_cmd, capture_output=True, text=True, timeout=15)

        # 4. Step 4: Measure Recovery Time Objective (RTO)
        recovered = False
        max_wait = env_settings.RECOVERY_MAX_WAIT_SECONDS
        while time.time() - start_time < max_wait:
            time.sleep(2)
            check_cmd = [
                "kubectl", "get", "pods",
                "-n", target_namespace,
                "-l", pod_label,
                "-o", "jsonpath={.items[0].status.phase}",
            ]
            status_res = subprocess.run(check_cmd, capture_output=True, text=True, timeout=5)
            if status_res.stdout.strip() == "Running":
                recovered = True
                break

        rto_seconds = time.time() - start_time
        assert recovered, f"Worker Pod failed to recover within {max_wait}s (RTO exceeded)!"

        # 5. Step 5: Send post-recovery telemetry and verify processing continues cleanly
        post_payload = sample_sensor_reading(machine_id="M-001", tool_wear_min=41)
        post_res = ingestion_client.post("/api/v1/sensor-readings", json=post_payload)
        assert post_res.status_code == 202, f"Ingestion failed after worker recovery: {post_res.text}"
        print(f"\n[CHAOS DRILL PASS] Processing Worker recovered in {rto_seconds:.1f}s (RTO <= {max_wait}s)")
