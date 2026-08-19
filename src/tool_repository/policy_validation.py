from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICIES = (
    "milestone-policy.md",
    "adapter-admission-policy.md",
    "knowledge-policy.md",
    "prompt-data-policy.md",
    "release-and-change-policy.md",
)
TRIAD_TEMPLATE = "docs/milestone_review_triad.md"
TRIAD_INSTRUCTION = "AGENTS.md"


def validate_policy_docs(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    policy_root = root / "docs" / "policies"
    index = policy_root / "README.md"
    if not index.exists():
        issues.append("policy index is missing")
    index_text = index.read_text(encoding="utf-8") if index.exists() else ""
    for filename in POLICIES:
        path = policy_root / filename
        if not path.exists():
            issues.append(f"policy is missing: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in ("**Version:**", "**Owner:**", "**Review:**", "**Enforcement:**"):
            if marker not in text:
                issues.append(f"{filename}: missing metadata {marker}")
        if filename not in index_text:
            issues.append(f"policy index does not link to {filename}")
    template = root / TRIAD_TEMPLATE
    if not template.exists() or "| AI Engineer |" not in template.read_text(encoding="utf-8"):
        issues.append("milestone review triad template is missing or incomplete")
    instruction = root / TRIAD_INSTRUCTION
    if not instruction.exists() or "mandatory review triad" not in instruction.read_text(encoding="utf-8").lower():
        issues.append("Codex review triad executor instruction is missing or incomplete")
    return issues
