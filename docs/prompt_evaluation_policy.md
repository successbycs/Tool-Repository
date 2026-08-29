# Prompt evaluation policy

## Required evidence

Every reusable prompt evaluation must identify:

- fixture set ID, version, SHA-256, and non-sensitive data classification;
- prompt ID and version, plus its resolved definition hash;
- rubric ID, version, dimensions, weights, and regression thresholds;
- evaluator runtime and named settings profile;
- sample size and a passed calibration reference;
- baseline, candidate, and correction comparison results; and
- known limitations.

The checked-in fixture is deliberately synthetic. It proves this evaluation
mechanism, not real-world model quality or production readiness.

## Calibration

Calibration is passed only when the named evaluator/settings profile has been
checked against an approved, non-sensitive fixture and the fixture identifies
the comparison reference. A failed, missing, or untraceable calibration blocks
the report.

## Thresholds and promotion

For the reference rubric, candidate drift is detected when the weighted
overall drop is at least `0.15` or a dimension drop is at least `0.20`.
Corrections must keep every baseline drop at or below `0.05`. These values are
versioned with the rubric and must be reviewed when changed.

A passing non-regression comparison does **not** promote a prompt. A proposal
remains `proposed` until a human reviewer approves the evidence, risks,
limitations, and semantic-version change. Production data stays in the owning
solution's controlled evaluation system and is represented here only by safe
references and hashes where permitted.

Run the deterministic fixture report with:

```bash
PYTHONPATH=src python3 -m tool_repository prompts evaluate \
  --fixture examples/prompt-evaluation-fixture
```
