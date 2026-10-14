#!/usr/bin/env python3
"""Rebuild rag/vectors.json by embedding the corpus through the deployed site.

Why this is not a local script: the embeddings come from Workers AI, and the
deploy token deliberately carries no Workers AI permission. Inside a Pages
Function the `AI` binding needs no token at all, so the index is built by the
site itself through /api/reindex, which stays closed unless RAG_ADMIN_SECRET
is set on the project.

The sequence, and why each step is there:

  1. Set a one-shot RAG_ADMIN_SECRET on the project.  Pages applies
     environment changes to *new* deployments, so a secret set now is not
     visible to the deployment already serving.
  2. Deploy.  This is the deployment that can see the secret.
  3. POST /api/reindex, write rag/vectors.json.
  4. Remove the secret, closing the endpoint again on the next deploy.
  5. Commit and push: CI deploys the new index, and that deployment has no
     secret, so /api/reindex answers 404 from then on.

    CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... \\
        python3 scripts/reindex_vectors.py [--project vladimir-portfolio]

Reads .env if the variables are not already exported.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import secrets
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
CORPUS = ROOT / "rag" / "corpus.json"
VECTORS = ROOT / "rag" / "vectors.json"
from build_corpus import digest  # noqa: E402  (needs ROOT on sys.path)

API = "https://api.cloudflare.com/client/v4"
# Cloudflare answers 403 to a bare urllib user agent.
UA = "Mozilla/5.0 (X11; Linux x86_64) portfolio-reindex"
# Not the pages.dev hostname: functions/_middleware.ts 301s it to here, and
# urllib would follow that redirect as a GET, which /api/reindex does not route.
DEFAULT_ORIGIN = "https://vladimir.ladetec.com"


def env(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            key, _, raw = line.partition("=")
            if key.strip() == name:
                return raw.strip().strip("'\"")
    sys.exit(f"{name} is not set, and .env does not carry it")


def api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def set_secret(token: str, account: str, project: str, value: str | None) -> None:
    variable = {"type": "secret_text", "value": value} if value else None
    body = {
        "deployment_configs": {
            stage: {"env_vars": {"RAG_ADMIN_SECRET": variable}}
            for stage in ("production", "preview")
        }
    }
    result = api("PATCH", f"/accounts/{account}/pages/projects/{project}", token, body)
    if not result.get("success"):
        sys.exit(f"could not set the secret: {result.get('errors')}")


def deploy(project: str) -> None:
    wrangler = os.environ.get("WRANGLER", "pnpm dlx wrangler@latest").split()
    command = [*wrangler, "pages", "deploy", "--project-name", project, "--commit-dirty=true"]
    print("  $", " ".join(command))
    environment = {
        **os.environ,
        "CI": "1",
        "NO_UPDATE_NOTIFIER": "1",
        "WRANGLER_SEND_METRICS": "false",
    }
    # Wrangler lingers after reporting success; the deployment is already made.
    try:
        finished = subprocess.run(command, cwd=ROOT, env=environment, timeout=240, check=False)
    except subprocess.TimeoutExpired:
        print("  (wrangler did not exit; the deployment was already submitted)")
        return
    # A deploy that did not happen is not a harmless step to skip: the secret is
    # only visible to a *new* deployment, so /api/reindex would answer 404 from
    # the one still serving, several minutes later and with no obvious cause.
    if finished.returncode != 0:
        sys.exit(
            f"wrangler exited {finished.returncode} without deploying, so the running "
            "deployment cannot see the secret. If the npm registry is unreachable from "
            "here, point WRANGLER at a cached install and run this again:\n"
            "  WRANGLER='node ~/.cache/pnpm/dlx/<hash>/pkg/node_modules/wrangler/bin/wrangler.js'"
        )


def reindex(origin: str, secret: str) -> dict:
    request = urllib.request.Request(
        f"{origin}/api/reindex",
        data=b"",
        headers={"Authorization": f"Bearer {secret}", "User-Agent": UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        sys.exit(f"/api/reindex answered {err.code}: {err.read()[:300]!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="vladimir-portfolio")
    parser.add_argument(
        "--origin",
        help=f"Origin to call. Defaults to {DEFAULT_ORIGIN}.",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="The running deployment already carries the secret.",
    )
    args = parser.parse_args()
    origin = args.origin or DEFAULT_ORIGIN

    token = env("CLOUDFLARE_API_TOKEN")
    account = env("CLOUDFLARE_ACCOUNT_ID")
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    secret = secrets.token_urlsafe(32)

    print(f"1. opening /api/reindex on {args.project}")
    set_secret(token, account, args.project, secret)
    try:
        if not args.skip_deploy:
            print("2. deploying so the secret is visible to the running code")
            deploy(args.project)
        print(f"3. embedding {len(corpus)} chunks through {origin}")
        result = reindex(origin, secret)

        ids = [c["id"] for c in corpus]
        if result.get("ids") != ids:
            sys.exit("the deployed corpus is not the one on disk — deploy first, then reindex")
        blob = base64.b64decode(result["b64"])
        expected = result["count"] * result["dims"]
        if len(blob) != expected:
            sys.exit(f"index is {len(blob)} bytes, expected {expected}")

        VECTORS.write_text(
            json.dumps(
                {
                    "model": "@cf/baai/bge-m3",
                    "dims": result["dims"],
                    "count": result["count"],
                    "ids": ids,
                    "digest": digest(corpus),
                    "b64": result["b64"],
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"   wrote {VECTORS.relative_to(ROOT)}: {result['count']} x {result['dims']}")
    finally:
        print("4. closing /api/reindex")
        set_secret(token, account, args.project, None)

    print("5. commit rag/vectors.json and push — CI deploys the index, with no secret")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
