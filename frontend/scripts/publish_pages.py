"""Build and publish frontend-only artifacts without Actions/workflow scope."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1]
ROOT = FRONTEND.parent


def run(args, cwd=None, capture=False, check=True, payload=None):
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        input=payload,
    )


def publish(repository, build=True):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Use owner/repository")
    owner, name = repository.split("/")
    base = "/" if name.lower() == owner.lower() + ".github.io" else f"/{name}/"
    if build:
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        run([npm, "run", "build:pages", "--", "--base", base], cwd=FRONTEND)
    dist = FRONTEND / "dist-pages"
    if not (dist / "index.html").is_file() or f"{base}assets/" not in (
        dist / "index.html"
    ).read_text(encoding="utf-8"):
        raise ValueError("Build output is missing or uses a different base path")
    secret_values = []
    env = ROOT / "backend/.env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if (
                key
                in {
                    "DATABASE_URL",
                    "TEST_DATABASE_URL",
                    "JWT_SECRET",
                    "ADMIN_PASSWORD",
                    "DEMO_PASSWORD",
                }
                and value
            ):
                secret_values.append(value.encode())
    for path in dist.rglob("*"):
        if path.is_file() and (
            path.name.startswith(".env")
            or path.suffix == ".secret"
            or any(value in path.read_bytes() for value in secret_values)
        ):
            raise ValueError("Private configuration found in build output")

    # This independent repository stages only compiled files, never the course worktree.
    staging = Path(tempfile.mkdtemp(prefix="scu-pages-publish-"))
    shutil.copytree(dist, staging, dirs_exist_ok=True)
    (staging / ".nojekyll").write_text("", encoding="utf-8")
    remote = f"https://github.com/{repository}.git"
    run(["git", "init", "-q", "-b", "gh-pages"], staging)
    run(["git", "config", "user.name", owner], staging)
    run(["git", "config", "user.email", owner + "@users.noreply.github.com"], staging)
    run(["git", "config", "core.autocrlf", "false"], staging)
    run(["git", "remote", "add", "origin", remote], staging)
    previous = run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", "gh-pages"], staging, True, False
    )
    if previous.returncode == 0:
        run(["git", "fetch", "--quiet", "origin", "gh-pages"], staging)
        run(["git", "reset", "--mixed", "FETCH_HEAD"], staging, True)
    elif previous.returncode != 2:
        raise RuntimeError(previous.stderr)
    run(["git", "add", "--all"], staging)
    changed = run(["git", "diff", "--cached", "--quiet"], staging, check=False)
    if changed.returncode:
        run(["git", "commit", "-q", "-m", "Deploy Swiss frontend guest preview"], staging)
    run(["git", "push", "origin", "HEAD:refs/heads/gh-pages"], staging)
    commit = run(["git", "rev-parse", "HEAD"], staging, True).stdout.strip()

    endpoint = f"repos/{repository}/pages"
    current = run(["gh", "api", endpoint], capture=True, check=False)
    if current.returncode and "404" not in current.stderr:
        raise RuntimeError(current.stderr)
    method = "POST" if current.returncode else "PUT"
    config = {"source": {"branch": "gh-pages", "path": "/"}, "build_type": "legacy"}
    result = run(
        ["gh", "api", "--method", method, endpoint, "--input", "-"],
        capture=True,
        check=False,
        payload=json.dumps(config),
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    # GitHub can acknowledge a Pages update with an empty 204 response.
    website = (
        json.loads(result.stdout)
        if result.stdout.strip()
        else json.loads(run(["gh", "api", endpoint], capture=True).stdout)
    )
    return {"repository": repository, "url": website.get("html_url"), "commit": commit}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="Danielliu1219/scu-db-ecommerce-order-system")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    print(json.dumps(publish(args.repo, not args.skip_build), ensure_ascii=False))
