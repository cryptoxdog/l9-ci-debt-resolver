"""Post-run hook: dispatch corpus-update event to l9-ci-debt-intelligence after a successful resolver run."""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

INTELLIGENCE_REPO = "cryptoxdog/l9-ci-debt-intelligence"
DISPATCH_EVENT_TYPE = "corpus-update"

PAYLOAD_SCHEMA = {
    "event_type": DISPATCH_EVENT_TYPE,
    "client_payload": {
        "source_repo": "cryptoxdog/l9-ci-debt-resolver",
        "artifact_kind": "resolver_findings",
        "findings_path": "reports/PR_REMEDIATION_FINDINGS.jsonl",
        "convergence_path": "reports/PR_REMEDIATION_CONVERGENCE_REPORT.md",
        "source_sha": "<resolver_commit_sha>",
        "run_id": "<github_actions_run_id>",
    },
}


def build_payload(source_sha: str, run_id: str) -> dict:
    payload = json.loads(json.dumps(PAYLOAD_SCHEMA))
    payload["client_payload"]["source_sha"] = source_sha
    payload["client_payload"]["run_id"] = run_id
    return payload


def dispatch(token: str, payload: dict, dry_run: bool = False) -> int:
    url = f"https://api.github.com/repos/{INTELLIGENCE_REPO}/dispatches"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    if dry_run:
        print(f"[dry-run] Would POST to {url}")
        print(f"[dry-run] Payload: {json.dumps(payload, indent=2)}")
        return 0

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            print(f"[post_run_hook] Dispatched corpus-update → {INTELLIGENCE_REPO} (HTTP {status})")
            return 0
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        print(f"[post_run_hook] DISPATCH FAILED HTTP {exc.code}: {body_text}", file=sys.stderr)
        print("[post_run_hook] Resolver run remains valid. Downstream handoff failed.", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch corpus-update to l9-ci-debt-intelligence.")
    parser.add_argument("--source-sha", required=True, help="Resolver commit SHA")
    parser.add_argument("--run-id", required=True, help="GitHub Actions run ID")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without dispatching")
    args = parser.parse_args()

    token = os.environ.get("L9_INTELLIGENCE_DISPATCH_TOKEN", "")
    if not token and not args.dry_run:
        print("[post_run_hook] ERROR: L9_INTELLIGENCE_DISPATCH_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    payload = build_payload(source_sha=args.source_sha, run_id=args.run_id)
    rc = dispatch(token=token, payload=payload, dry_run=args.dry_run)
    sys.exit(rc)


if __name__ == "__main__":
    main()
