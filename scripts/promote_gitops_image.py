#!/usr/bin/env python3
"""Script to promote a verified container image tag into MaintAI-gitops environment.

Usage:
    python scripts/promote_gitops_image.py --env production --tag sha-a995109 --token $GITOPS_SYNC_TOKEN
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def promote_image(target_env: str, image_tag: str, token: str, gitops_repo: str = "chiendz11/MaintAI-gitops"):
    print(f"Promoting image tag '{image_tag}' to environment '{target_env}' in '{gitops_repo}'...")

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_url = f"https://x-access-token:{token}@github.com/{gitops_repo}.git" if token else f"git@github.com:{gitops_repo}.git"

        # Clone target repo
        res = subprocess.run(["git", "clone", "--depth", "1", clone_url, tmpdir], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Failed to clone GitOps repo: {res.stderr}")
            sys.exit(1)

        repo_path = Path(tmpdir)
        env_kustomization = repo_path / "environments" / target_env / "apps" / "kustomization.yaml"

        if not env_kustomization.exists():
            print(f"Kustomization file not found at {env_kustomization}, falling back to local overlay")
            env_kustomization = repo_path / "environments" / "local" / "apps" / "kustomization.yaml"

        if not env_kustomization.exists():
            print(f"Could not locate kustomization file in {target_env}")
            sys.exit(1)

        content = env_kustomization.read_text(encoding="utf-8")
        # Replace image tags
        import re
        # Pattern to replace newTag: <anything> with newTag: <image_tag>
        updated_content = re.sub(r"newTag:\s*['\"]?[\w\-\.]+['\"]?", f"newTag: '{image_tag}'", content)
        env_kustomization.write_text(updated_content, encoding="utf-8")

        # Commit and push
        subprocess.run(["git", "config", "user.name", "MaintAI Release Orchestrator"], cwd=tmpdir)
        subprocess.run(["git", "config", "user.email", "release-bot@maintai.internal"], cwd=tmpdir)
        subprocess.run(["git", "add", "."], cwd=tmpdir)

        diff = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True, cwd=tmpdir)
        if not diff.stdout.strip():
            print("No changes needed. GitOps is already on this image tag.")
            return

        commit_msg = f"chore(release): promote images to {target_env} tag={image_tag}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=tmpdir, check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], cwd=tmpdir, check=True)
        print(f"Successfully promoted image tag '{image_tag}' to {target_env}!")


def main():
    parser = argparse.ArgumentParser(description="Promote image tag to GitOps")
    parser.add_argument("--env", default="production", help="Target GitOps environment")
    parser.add_argument("--tag", required=True, help="Docker image tag (e.g. sha-xxxx or v1.4.0)")
    parser.add_argument("--token", default=os.environ.get("GITOPS_SYNC_TOKEN", ""), help="GitHub token with repo push rights")
    parser.add_argument("--repo", default="chiendz11/MaintAI-gitops", help="GitOps repo name")
    args = parser.parse_args()

    promote_image(args.env, args.tag, args.token, args.repo)


if __name__ == "__main__":
    main()
