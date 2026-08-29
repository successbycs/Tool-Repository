from __future__ import annotations

import json
import hashlib
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "milestone_registry.json"
VALID_STATUSES = {"not_started", "in_progress", "blocked", "complete"}
REQUIRED_MILESTONE_FIELDS = {
    "id", "title", "delivery_type", "status", "capability_unblocked", "dependencies",
    "risk_level", "review_requirements", "write_scope", "required_artifacts", "proof_artifact",
    "verify", "execution_brief", "ingestion",
}
REQUIRED_BRIEF_FIELDS = {
    "objective", "context", "non_goals", "required_outputs", "proof_requirements",
    "verification_commands", "stop_conditions",
}
REQUIRED_PROOF_FIELDS = {
    "milestone_id", "implementation_revision", "generated_at", "environment", "status", "verification", "observed_result",
}
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
INGESTION_ASSET_TYPES = {"adapter", "goal", "local_model", "prompt", "template", "harvested_asset"}
INGESTION_EFFECTS = {"publish", "retire", "not_published"}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_brief(milestone: dict[str, Any], issues: list[str]) -> None:
    brief = milestone.get("execution_brief")
    label = milestone.get("id", "<unknown>")
    if not isinstance(brief, dict):
        issues.append(f"{label}: execution_brief must be an object")
        return
    missing = REQUIRED_BRIEF_FIELDS - set(brief)
    if missing:
        issues.append(f"{label}: execution_brief missing {', '.join(sorted(missing))}")
        return
    if not isinstance(brief["objective"], str) or not brief["objective"].strip():
        issues.append(f"{label}: execution_brief.objective must be a non-empty string")
    if not isinstance(brief["context"], dict):
        issues.append(f"{label}: execution_brief.context must be an object")
    for key in REQUIRED_BRIEF_FIELDS - {"objective", "context"}:
        if not _is_string_list(brief[key]):
            issues.append(f"{label}: execution_brief.{key} must be a non-empty string list")


def _validate_ingestion(milestone: dict[str, Any], issues: list[str]) -> None:
    label = milestone.get("id", "<unknown>")
    ingestion = milestone.get("ingestion")
    required = {"applies", "asset_types", "source_records", "verification", "catalogue_effect"}
    if not isinstance(ingestion, dict) or set(ingestion) != required:
        issues.append(f"{label}: ingestion must contain only applies, asset_types, source_records, verification, and catalogue_effect")
        return
    applies = ingestion["applies"]
    if not isinstance(applies, bool):
        issues.append(f"{label}: ingestion.applies must be a boolean")
        return
    for key in ("asset_types", "source_records", "verification"):
        if not isinstance(ingestion[key], list) or any(not isinstance(item, str) or not item.strip() for item in ingestion[key]):
            issues.append(f"{label}: ingestion.{key} must be a string list")
    if applies:
        if not ingestion["asset_types"] or not set(ingestion["asset_types"]).issubset(INGESTION_ASSET_TYPES):
            issues.append(f"{label}: ingestion.asset_types must name supported ingested asset types")
        if not ingestion["source_records"] or not ingestion["verification"]:
            issues.append(f"{label}: applicable ingestion requires source_records and verification")
        if ingestion["catalogue_effect"] not in INGESTION_EFFECTS:
            issues.append(f"{label}: applicable ingestion.catalogue_effect must be publish, retire, or not_published")
    elif ingestion["asset_types"] or ingestion["source_records"] or ingestion["verification"] or ingestion["catalogue_effect"] != "not_applicable":
        issues.append(f"{label}: non-applicable ingestion must use empty lists and catalogue_effect not_applicable")


def validate_registry(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    try:
        payload = _load_json(root / "milestone_registry.json")
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot load milestone registry: {error}"]
    milestones = payload.get("milestones") if isinstance(payload, dict) else None
    if not isinstance(milestones, list):
        return ["milestone_registry.json must contain a milestones list"]
    ids: set[str] = set()
    records: dict[str, dict[str, Any]] = {}
    for milestone in milestones:
        if not isinstance(milestone, dict):
            issues.append("milestone registry contains a non-object entry")
            continue
        identifier = str(milestone.get("id") or "").strip()
        if not identifier or identifier in ids:
            issues.append(f"duplicate or empty milestone id: {identifier or '<empty>'}")
            continue
        ids.add(identifier)
        records[identifier] = milestone
        missing = REQUIRED_MILESTONE_FIELDS - set(milestone)
        if missing:
            issues.append(f"{identifier}: missing fields {', '.join(sorted(missing))}")
        if milestone.get("status") not in VALID_STATUSES:
            issues.append(f"{identifier}: invalid status {milestone.get('status')!r}")
        for key in ("dependencies", "write_scope", "required_artifacts", "verify"):
            if not _is_string_list(milestone.get(key)):
                issues.append(f"{identifier}: {key} must be a string list")
        if any("<" in value or ">" in value for value in milestone.get("required_artifacts", [])):
            issues.append(f"{identifier}: required_artifacts must use concrete paths, not placeholders")
        if milestone.get("risk_level") not in {"low", "moderate", "high"}:
            issues.append(f"{identifier}: risk_level must be low, moderate, or high")
        review = milestone.get("review_requirements")
        if not isinstance(review, dict) or not isinstance(review.get("required"), bool) or not _is_string_list(review.get("roles", [])):
            issues.append(f"{identifier}: review_requirements must contain boolean required and string-list roles")
        _validate_brief(milestone, issues)
        _validate_ingestion(milestone, issues)
    for identifier, milestone in records.items():
        for dependency in milestone.get("dependencies", []):
            if dependency not in records:
                issues.append(f"{identifier}: unknown dependency {dependency}")
            elif dependency == identifier:
                issues.append(f"{identifier}: cannot depend on itself")
        if milestone.get("status") == "complete":
            issues.extend(close_check(identifier, root=root, registry=records))
    summary = payload.get("milestone_status_summary")
    if summary is not None:
        expected_summary = [
            {
                "id": str(milestone.get("id") or ""),
                "status": milestone.get("status"),
                "title": milestone.get("title"),
            }
            for milestone in milestones
            if isinstance(milestone, dict)
        ]
        if summary != expected_summary:
            issues.append("milestone_status_summary must exactly match the ordered milestone IDs, titles, and statuses")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visited:
            return
        if identifier in visiting:
            issues.append(f"dependency cycle includes {identifier}")
            return
        visiting.add(identifier)
        for dependency in records[identifier].get("dependencies", []):
            if dependency in records:
                visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in records:
        visit(identifier)
    return issues


def _validate_proof(path: Path, identifier: str) -> list[str]:
    try:
        proof = _load_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return [f"{identifier}: cannot load proof artifact {path}: {error}"]
    if not isinstance(proof, dict):
        return [f"{identifier}: proof artifact must be an object"]
    missing = REQUIRED_PROOF_FIELDS - set(proof)
    if missing:
        return [f"{identifier}: proof artifact missing {', '.join(sorted(missing))}"]
    issues: list[str] = []
    if proof.get("milestone_id") != identifier:
        issues.append(f"{identifier}: proof milestone_id does not match")
    if proof.get("status") != "passed":
        issues.append(f"{identifier}: proof status must be passed")
    try:
        datetime.fromisoformat(str(proof.get("generated_at")).replace("Z", "+00:00"))
    except ValueError:
        issues.append(f"{identifier}: proof generated_at must be ISO-8601")
    checks = proof.get("verification")
    if not isinstance(checks, list) or not checks:
        issues.append(f"{identifier}: proof verification must be a non-empty list")
    else:
        for index, item in enumerate(checks):
            if (
                not isinstance(item, dict)
                or item.get("exit_code") != 0
                or not str(item.get("command") or "").strip()
                or not str(item.get("output_sha256") or "").strip()
            ):
                issues.append(f"{identifier}: proof verification must contain successful command records")
                break
            output = item.get("output")
            if not isinstance(output, str):
                issues.append(f"{identifier}: proof verification[{index}].output must be recorded")
            elif hashlib.sha256(output.encode("utf-8")).hexdigest() != item["output_sha256"]:
                issues.append(f"{identifier}: proof verification[{index}] output hash does not match output")
    return issues


def _safe_repository_file(root: Path, reference: object) -> Path | None:
    if not isinstance(reference, str) or not reference.strip():
        return None
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved if resolved.is_file() else None


def _validate_integrity_v2(root: Path, proof: dict[str, Any], milestone: dict[str, Any], identifier: str) -> list[str]:
    """Validate proof data that is bound to an inspectable revision and review files."""

    issues: list[str] = []
    revision = proof.get("implementation_revision")
    if not isinstance(revision, str) or not _COMMIT.fullmatch(revision):
        issues.append(f"{identifier}: proof implementation_revision must be a full Git commit SHA")
    else:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            issues.append(f"{identifier}: proof implementation_revision is not an inspectable Git commit")
    review = milestone["review_requirements"]
    if not review["required"]:
        return issues
    records = proof.get("reviews")
    if not isinstance(records, list):
        return [*issues, f"{identifier}: proof reviews must be a list"]
    by_role: dict[str, dict[str, Any]] = {}
    for record in records:
        if isinstance(record, dict) and isinstance(record.get("role"), str):
            by_role[record["role"]] = record
    for role in review["roles"]:
        record = by_role.get(role)
        if record is None or record.get("status") != "passed":
            issues.append(f"{identifier}: required review missing or failed for {role}")
            continue
        review_path = _safe_repository_file(root, record.get("reference"))
        if review_path is None:
            issues.append(f"{identifier}: {role} review reference must be an existing repository-contained file")
            continue
        digest = record.get("content_sha256")
        actual = hashlib.sha256(review_path.read_bytes()).hexdigest()
        if not isinstance(digest, str) or digest != actual:
            issues.append(f"{identifier}: {role} review content hash does not match its saved record")
    return issues


def close_check(
    identifier: str,
    *,
    root: Path = ROOT,
    registry: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    records = registry
    if records is None:
        try:
            payload = _load_json(root / "milestone_registry.json")
            records = {str(item.get("id")): item for item in payload["milestones"] if isinstance(item, dict)}
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            return [f"cannot load milestone registry: {error}"]
    milestone = records.get(identifier)
    if milestone is None:
        return [f"unknown milestone {identifier}"]
    issues: list[str] = []
    for dependency in milestone.get("dependencies", []):
        if records.get(dependency, {}).get("status") != "complete":
            issues.append(f"{identifier}: dependency {dependency} is not complete")
    for relative_path in milestone.get("required_artifacts", []):
        if not (root / relative_path).exists():
            issues.append(f"{identifier}: required artifact missing {relative_path}")
    proof_path = root / str(milestone.get("proof_artifact") or "")
    if not proof_path.exists():
        issues.append(f"{identifier}: proof artifact missing {milestone.get('proof_artifact')}")
    else:
        proof_issues = _validate_proof(proof_path, identifier)
        issues.extend(proof_issues)
        if proof_issues:
            return issues
        proof = _load_json(proof_path)
        expected = milestone["execution_brief"]["verification_commands"]
        recorded = {str(item.get("command") or "") for item in proof.get("verification", []) if isinstance(item, dict)}
        for command in expected:
            if command not in recorded:
                issues.append(f"{identifier}: proof is missing verification record for {command}")
        ingestion = milestone["ingestion"]
        if ingestion["applies"]:
            for source in ingestion["source_records"]:
                if "://" not in source and not (root / source).exists():
                    issues.append(f"{identifier}: ingestion source record is missing {source}")
            for command in ingestion["verification"]:
                if command not in recorded:
                    issues.append(f"{identifier}: proof is missing ingestion verification record for {command}")
        review = milestone["review_requirements"]
        if review["required"]:
            completed_roles = {
                str(item.get("role") or "")
                for item in proof.get("reviews", [])
                if isinstance(item, dict) and item.get("status") == "passed"
            }
            for role in review["roles"]:
                if role not in completed_roles:
                    issues.append(f"{identifier}: required review missing or failed for {role}")
        if milestone.get("proof_integrity_version") == "2.0":
            issues.extend(_validate_integrity_v2(root, proof, milestone, identifier))
    return issues
