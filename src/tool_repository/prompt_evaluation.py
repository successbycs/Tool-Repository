"""Deterministic, privacy-safe prompt drift evaluation from fixed score fixtures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, SchemaError

from tool_repository.prompt_library import DEFAULT_DEFINITIONS_PATH, load_prompt_library


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "prompt-evaluation.schema.json"
_SENSITIVE_LITERAL = re.compile(r"(?:api[_-]?key|password|token|secret)\s*[:=]\s*\S+|authorization\s*:\s*bearer\s+\S+|bearer\s+[A-Za-z0-9._-]{10,}", re.I)


def _read_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number {value}"))), []
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{path}: cannot read JSON: {error}"]


def _privacy_issues(value: Any, path: str = "evaluation") -> list[str]:
    if isinstance(value, str):
        return [f"{path} appears to contain a secret literal"] if _SENSITIVE_LITERAL.search(value) else []
    if isinstance(value, list):
        return [issue for index, item in enumerate(value) for issue in _privacy_issues(item, f"{path}[{index}]")]
    if isinstance(value, dict):
        return [issue for key, item in value.items() for issue in _privacy_issues(item, f"{path}.{key}")]
    return []


def validate_evaluation_fixture(payload: Any, definitions: dict[tuple[str, str], dict[str, Any]] | None = None) -> list[str]:
    """Validate evaluation metadata, score sets, calibration, and prompt binding."""

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as error:
        return [f"prompt evaluation schema is invalid: {error}"]
    issues = [
        f"schema {'.'.join(str(part) for part in error.absolute_path) or 'evaluation'}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: (list(item.absolute_path), item.message))
    ]
    issues.extend(_privacy_issues(payload))
    if not isinstance(payload, dict):
        return issues
    rubric = payload.get("rubric")
    samples = payload.get("samples")
    if isinstance(rubric, dict) and isinstance(samples, list):
        dimensions = rubric.get("dimensions")
        if isinstance(dimensions, list):
            identifiers = [item.get("id") for item in dimensions if isinstance(item, dict)]
            if len(identifiers) != len(dimensions) or len(set(identifiers)) != len(identifiers):
                issues.append("rubric dimensions must have unique IDs")
            weights = [item.get("weight") for item in dimensions if isinstance(item, dict) and isinstance(item.get("weight"), (int, float))]
            if weights and abs(sum(weights) - 1.0) > 1e-9:
                issues.append("rubric dimension weights must sum to 1.0")
            expected = set(identifiers)
            for index, sample in enumerate(samples):
                if not isinstance(sample, dict):
                    continue
                for field in ("baseline_scores", "candidate_scores", "corrected_scores"):
                    scores = sample.get(field)
                    if isinstance(scores, dict) and set(scores) != expected:
                        issues.append(f"samples[{index}].{field} must contain exactly the rubric dimension IDs")
    if definitions is not None:
        prompt = payload.get("prompt")
        if isinstance(prompt, dict) and (prompt.get("id"), prompt.get("version")) not in definitions:
            issues.append("evaluation prompt id/version is not in the validated prompt library")
    return issues


def _mean(samples: list[dict[str, Any]], field: str, dimension: str) -> float:
    return sum(float(sample[field][dimension]) for sample in samples) / len(samples)


def _weighted_score(means: dict[str, float], weights: dict[str, float]) -> float:
    return sum(means[identifier] * weights[identifier] for identifier in weights)


def evaluate_fixture(fixture_path: Path, *, definitions_path: Path = DEFAULT_DEFINITIONS_PATH) -> tuple[dict[str, Any] | None, list[str]]:
    """Evaluate baseline, candidate, and correction score sets deterministically."""

    payload, read_issues = _read_json(fixture_path)
    if payload is None:
        return None, read_issues
    definitions, definition_issues = load_prompt_library(definitions_path)
    issues = [*read_issues, *definition_issues, *validate_evaluation_fixture(payload, definitions)]
    if issues or not isinstance(payload, dict):
        return None, issues
    rubric = payload["rubric"]
    samples = payload["samples"]
    dimensions = rubric["dimensions"]
    weights = {item["id"]: float(item["weight"]) for item in dimensions}
    threshold = rubric["thresholds"]
    summaries: list[dict[str, Any]] = []
    candidate_events: list[dict[str, Any]] = []
    correction_events: list[dict[str, Any]] = []
    baseline_means: dict[str, float] = {}
    candidate_means: dict[str, float] = {}
    corrected_means: dict[str, float] = {}
    for identifier in weights:
        baseline = _mean(samples, "baseline_scores", identifier)
        candidate = _mean(samples, "candidate_scores", identifier)
        corrected = _mean(samples, "corrected_scores", identifier)
        candidate_drop = baseline - candidate
        corrected_drop = baseline - corrected
        baseline_means[identifier] = baseline
        candidate_means[identifier] = candidate
        corrected_means[identifier] = corrected
        summaries.append({"id": identifier, "baseline_mean": baseline, "candidate_mean": candidate, "corrected_mean": corrected, "candidate_drop": candidate_drop, "corrected_drop": corrected_drop})
        if candidate_drop >= float(threshold["dimension_score_drop"]):
            candidate_events.append({"taxonomy": "dimension_regression", "dimension": identifier, "drop": candidate_drop, "threshold": float(threshold["dimension_score_drop"])})
        if corrected_drop > float(threshold["non_regression_max_drop"]):
            correction_events.append({"taxonomy": "correction_regression", "dimension": identifier, "drop": corrected_drop, "threshold": float(threshold["non_regression_max_drop"])})
    overall = {
        "baseline": _weighted_score(baseline_means, weights),
        "candidate": _weighted_score(candidate_means, weights),
        "corrected": _weighted_score(corrected_means, weights),
    }
    candidate_drop = overall["baseline"] - overall["candidate"]
    corrected_drop = overall["baseline"] - overall["corrected"]
    if candidate_drop >= float(threshold["overall_score_drop"]):
        candidate_events.append({"taxonomy": "overall_regression", "dimension": None, "drop": candidate_drop, "threshold": float(threshold["overall_score_drop"])})
    if corrected_drop > float(threshold["non_regression_max_drop"]):
        correction_events.append({"taxonomy": "overall_correction_regression", "dimension": None, "drop": corrected_drop, "threshold": float(threshold["non_regression_max_drop"])})
    prompt = payload["prompt"]
    definition = definitions[(prompt["id"], prompt["version"])]
    report = {
        "schema_version": "1.0.0",
        "fixture": {**payload["fixture"], "sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest()},
        "prompt": {**prompt, "definition_sha256": definition["sha256"]},
        "rubric": {"id": rubric["id"], "version": rubric["version"], "thresholds": threshold},
        "evaluator": {**payload["evaluator"], "sample_size": len(samples)},
        "dimensions": summaries,
        "overall": {**overall, "candidate_drop": candidate_drop, "corrected_drop": corrected_drop},
        "drift": {"detected": bool(candidate_events), "events": candidate_events},
        "correction": {"proposal": payload["correction_proposal"], "auto_promoted": False, "non_regression_passed": not correction_events, "events": correction_events},
        "limitations": payload["limitations"],
    }
    return report, []


def write_evaluation_report(fixture_path: Path, output_path: Path | None = None, *, definitions_path: Path = DEFAULT_DEFINITIONS_PATH) -> list[str]:
    report, issues = evaluate_fixture(fixture_path, definitions_path=definitions_path)
    if report is None:
        return issues
    path = output_path or fixture_path.parent / "evaluation-report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []
