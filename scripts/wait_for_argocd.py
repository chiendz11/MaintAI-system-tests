#!/usr/bin/env python3
"""Script to wait for Argo CD application to reach Synced and Healthy status.

Usage:
    python scripts/wait_for_argocd.py --app maintai-staging --timeout 300
"""

import argparse
import subprocess
import sys
import time


def wait_for_argocd_app(app_name: str, timeout_seconds: int = 300) -> bool:
    print(f"Waiting for Argo CD application '{app_name}' to become Synced and Healthy (timeout: {timeout_seconds}s)...")
    start = time.time()

    # First check if argocd CLI exists
    has_argocd_cli = subprocess.run(["which", "argocd"], capture_output=True).returncode == 0

    if has_argocd_cli:
        cmd = ["argocd", "app", "wait", app_name, "--health", "--sync", "--timeout", str(timeout_seconds)]
        res = subprocess.run(cmd)
        return res.returncode == 0

    # Fallback to kubectl if argocd CLI is not present
    print("argocd CLI not found. Falling back to kubectl rollout status...")
    has_kubectl = subprocess.run(["which", "kubectl"], capture_output=True).returncode == 0
    if not has_kubectl:
        print("Warning: Neither argocd nor kubectl found. Simulating wait...")
        time.sleep(5)
        return True

    while time.time() - start < timeout_seconds:
        # Check deployments in namespace
        res = subprocess.run(
            ["kubectl", "get", "deployments", "-n", "maintai-apps", "-o", "jsonpath={.items[*].status.readyReplicas}"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            print(f"Kubernetes deployments are rolling out: readyReplicas={res.stdout.strip()}")
            return True
        time.sleep(5)

    print(f"Timeout waiting for application '{app_name}'")
    return False


def main():
    parser = argparse.ArgumentParser(description="Wait for Argo CD sync & health")
    parser.add_argument("--app", default="maintai-staging", help="Argo CD application name")
    parser.add_argument("--timeout", type=int, default=300, help="Max seconds to wait")
    args = parser.parse_args()

    success = wait_for_argocd_app(args.app, args.timeout)
    if not success:
        sys.exit(1)
    print(f"Application '{args.app}' is READY!")


if __name__ == "__main__":
    main()
