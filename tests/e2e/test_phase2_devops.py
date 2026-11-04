"""System Tests for MaintAI Phase 2 (Enterprise DevOps & AWS Parity).

Tests cover the 4 core infrastructure pillars:
1. Secrets Management (LocalStack + External Secrets Operator)
2. Edge Routing (Ingress-NGINX with ALB simulation)
3. Autoscaling & K8s Policies (HPA, PDB, Zero-Trust NetworkPolicies)
4. Observability (Prometheus + Loki + Promtail + Grafana)
"""

import json
import os
import subprocess
from pathlib import Path
import pytest

NAMESPACE = os.getenv("NAMESPACE", "maintai-local")
KUBECONFIG = os.getenv("KUBECONFIG", "/home/chienqt/Dev/newBTL/Maint-infrastructure/local/.local/kubeconfig")


def run_kubectl(args: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ, KUBECONFIG=KUBECONFIG)
    return subprocess.run(
        ["kubectl"] + args,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class TestPillar1SecretsManagement:
    """Pillar 1: LocalStack Secrets Manager and External Secrets Operator (ESO)."""

    def test_cluster_secret_store_ready(self):
        result = run_kubectl(["get", "clustersecretstore", "aws-secrets-manager", "-o", "json"])
        assert result.returncode == 0, f"ClusterSecretStore aws-secrets-manager not found: {result.stderr}"
        data = json.loads(result.stdout)
        conditions = data.get("status", {}).get("conditions", [])
        is_ready = any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions)
        assert is_ready, f"ClusterSecretStore aws-secrets-manager is not Ready: {conditions}"

    def test_external_secrets_synced(self):
        result = run_kubectl(["get", "externalsecrets", "-n", NAMESPACE, "-o", "json"])
        assert result.returncode == 0, f"Failed to list ExternalSecrets in {NAMESPACE}: {result.stderr}"
        items = json.loads(result.stdout).get("items", [])
        assert len(items) > 0, f"No ExternalSecrets found in namespace {NAMESPACE}"

        synced_count = 0
        for item in items:
            name = item["metadata"]["name"]
            conditions = item.get("status", {}).get("conditions", [])
            ready = any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions)
            if ready:
                synced_count += 1
        assert synced_count == len(items), f"Not all ExternalSecrets are synced: {synced_count}/{len(items)}"


class TestPillar2EdgeRouting:
    """Pillar 2: Ingress-NGINX with AWS ALB simulation and virtual host routing."""

    def test_ingress_controller_and_class(self):
        result = run_kubectl(["get", "ingressclass", "alb", "-o", "json"])
        assert result.returncode == 0, f"IngressClass alb not found: {result.stderr}"

    def test_maintai_ingress_routes(self):
        result = run_kubectl(["get", "ingress", "maintai-ingress", "-n", NAMESPACE, "-o", "json"])
        assert result.returncode == 0, f"Ingress maintai-ingress not found in {NAMESPACE}: {result.stderr}"
        data = json.loads(result.stdout)
        assert data.get("spec", {}).get("ingressClassName") == "alb"

        rules = data.get("spec", {}).get("rules", [])
        hosts = {r.get("host") for r in rules}
        expected_hosts = {
            "app.maintai.local",
            "simulator.maintai.local",
            "api.maintai.local",
            "ingest.maintai.local",
            "processing.maintai.local",
        }
        missing = expected_hosts - hosts
        assert not missing, f"Missing virtual hosts in Ingress: {missing}"


class TestPillar3AutoscalingAndPolicies:
    """Pillar 3: HorizontalPodAutoscaler, PodDisruptionBudget, and NetworkPolicies."""

    def test_hpa_configured(self):
        result = run_kubectl(["get", "hpa", "-n", NAMESPACE, "-o", "json"])
        assert result.returncode == 0, f"Failed to list HPAs: {result.stderr}"
        items = json.loads(result.stdout).get("items", [])
        hpa_targets = {item["spec"]["scaleTargetRef"]["name"] for item in items}
        assert "business-api" in hpa_targets
        assert "processing-worker" in hpa_targets
        assert "ingestion-api" in hpa_targets

    def test_pdb_configured(self):
        result = run_kubectl(["get", "pdb", "-n", NAMESPACE, "-o", "json"])
        assert result.returncode == 0, f"Failed to list PDBs: {result.stderr}"
        items = json.loads(result.stdout).get("items", [])
        assert len(items) >= 2, f"Expected at least 2 PDBs, found {len(items)}"

    def test_zero_trust_network_policies(self):
        result = run_kubectl(["get", "netpol", "-n", NAMESPACE, "-o", "json"])
        assert result.returncode == 0, f"Failed to list NetworkPolicies: {result.stderr}"
        items = json.loads(result.stdout).get("items", [])
        policy_names = {item["metadata"]["name"] for item in items}
        assert "default-deny-all" in policy_names
        assert "allow-system-dns" in policy_names
        assert "allow-intra-namespace" in policy_names


class TestPillar4Observability:
    """Pillar 4: Logging with Loki + Promtail and Metrics with Prometheus."""

    def test_loki_and_promtail_running(self):
        result = run_kubectl(["get", "pods", "-n", NAMESPACE, "-l", "app in (loki, promtail)", "-o", "json"])
        assert result.returncode == 0, f"Failed to list Loki/Promtail pods: {result.stderr}"
        items = json.loads(result.stdout).get("items", [])
        assert len(items) >= 2, f"Expected both Loki and Promtail pods, found {len(items)}"
        for pod in items:
            phase = pod.get("status", {}).get("phase")
            assert phase == "Running", f"Pod {pod['metadata']['name']} is not Running (phase: {phase})"

    def test_loki_ready_endpoint(self):
        result = run_kubectl(["exec", "-n", NAMESPACE, "deploy/loki", "--", "wget", "-qO-", "http://localhost:3100/ready"])
        assert result.returncode == 0, f"Loki readiness check failed: {result.stderr}"
        assert "ready" in result.stdout.strip().lower()
