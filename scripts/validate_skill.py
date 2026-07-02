#!/usr/bin/env python3
"""
Deterministic structural validator for ci-debt-resolver skill pack.
Usage: python scripts/validate_skill.py <skill_root_dir>
Exits 0 if all gates pass. Exits 1 if any gate fails.
"""

import sys
import yaml
from pathlib import Path

REQUIRED_FILES = [
    "SKILL.md",
    "references/workflow-protocol.md",
    "references/classification-rules.md",
    "references/output-schema.md",
    "references/local-gate-protocol.md",
    "references/pr-treatment-protocol.md",
    "scripts/validate_skill.py",
]

REQUIRED_FRONTMATTER_FIELDS = [
    "name", "description", "skill_schema", "layer", "role",
    "tags", "owner", "status", "version", "updated"
]

REQUIRED_RESOURCE_MAP_LINKS = [
    "references/workflow-protocol.md",
    "references/classification-rules.md",
    "references/output-schema.md",
    "references/local-gate-protocol.md",
    "references/pr-treatment-protocol.md",
]

REQUIRED_SKILL_MD_SECTIONS = [
    "## Purpose",
    "## Authority Order",
    "## Core Invariants",
    "## Compact Workflow",
    "## Activation Signals",
    "## Expert Heuristics",
    "## Adapter Map",
    "## Output Artifacts",
    "## Failure Handling",
    "## Resource Map",
    "## Self-Improvement Hook",
]

# These markers are scanned in content files (not this script itself)
_STUB_MARKERS = ["TODO", "FIXME", "PLACEHOLDER", "raise NotImplementedError"]


def check(condition, gate, message, results):
    results.append({"gate": gate, "status": "PASS" if condition else "FAIL", "message": message})
    return condition


def validate(skill_root: Path):
    results = []

    for f in REQUIRED_FILES:
        check((skill_root / f).exists(), "required_files", f"{f} exists", results)

    skill_md = skill_root / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        if content.startswith("---"):
            end = content.index("---", 3)
            try:
                fm = yaml.safe_load(content[3:end])
                for field in REQUIRED_FRONTMATTER_FIELDS:
                    check(field in fm, "frontmatter", f"field '{field}' present", results)
                check(str(fm.get("name","")).islower(), "frontmatter", "name is lowercase", results)
                check(str(fm.get("description","")).islower(), "frontmatter", "description is lowercase", results)
            except Exception as e:
                check(False, "frontmatter", f"YAML parse error: {e}", results)

        for section in REQUIRED_SKILL_MD_SECTIONS:
            check(section in content, "sections", f"contains '{section}'", results)

        for link in REQUIRED_RESOURCE_MAP_LINKS:
            check(link in content, "resource_map", f"links to {link}", results)

    # Zero-stub scan — skip this validator script itself to avoid self-reference false positives
    scan_files = [
        f for f in list(skill_root.rglob("*.md")) + list(skill_root.rglob("*.yaml"))
        if f.suffix in {".md", ".yaml"}
    ]
    for fpath in scan_files:
        text = fpath.read_text(errors="replace")
        for marker in _STUB_MARKERS:
            check(marker not in text, "zero_stub",
                  f"No '{marker}' in {fpath.relative_to(skill_root)}", results)

    check(not (skill_root / "agents" / "openai.yaml").exists(),
          "no_deprecated_files", "agents/openai.yaml absent", results)

    for ref_file in (skill_root / "references").glob("*.md"):
        text = ref_file.read_text(errors="replace")
        check("L9_META" in text, "metadata", f"{ref_file.name} has L9_META", results)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    print(f"\n{'='*60}")
    print("ci-debt-resolver Skill Validation Report")
    print(f"{'='*60}")
    for r in results:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  [{r['gate']}] {icon} {r['message']}")
    print(f"{'='*60}")
    print(f"PASSED: {passed}  FAILED: {failed}  TOTAL: {passed + failed}")
    if failed == 0:
        print("TIER: exemplary")
        return 0
    elif failed <= 2:
        print("TIER: strong")
        return 1
    else:
        print("TIER: developing")
        return 1


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(validate(root))
