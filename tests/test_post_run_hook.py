"""Tests for post_run_hook payload generation and dry-run mode."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parents[1] / "scripts" / "post_run_hook.py"


def test_payload_schema():
    from scripts.post_run_hook import build_payload
    p = build_payload(source_sha="abc1234", run_id="999")
    assert p["event_type"] == "corpus-update"
    assert p["client_payload"]["source_sha"] == "abc1234"
    assert p["client_payload"]["run_id"] == "999"
    assert p["client_payload"]["artifact_kind"] == "resolver_findings"


def test_dry_run_exits_zero():
    result = subprocess.run(
        [sys.executable, str(HOOK), "--source-sha", "abc1234", "--run-id", "999", "--dry-run"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout


def test_no_token_without_dry_run_exits_nonzero(monkeypatch):
    import os
    env = {k: v for k, v in os.environ.items() if k != "L9_INTELLIGENCE_DISPATCH_TOKEN"}
    result = subprocess.run(
        [sys.executable, str(HOOK), "--source-sha", "abc1234", "--run-id", "999"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode != 0
