# Prompt drift model

Prompt drift is a measurable regression against a versioned baseline under a
fixed fixture set and rubric. It is not inferred from an opaque overall score
or a single model call.

The evaluator compares a baseline, a candidate, and a proposed correction on
each rubric dimension. The static report includes sample size, fixture version
and SHA-256, rubric version, evaluator runtime/settings profile, calibration
result, per-dimension means, weighted overall means, thresholds, and known
limitations.

## Taxonomy

| Event | Meaning | Response |
| --- | --- | --- |
| `dimension_regression` | A named dimension dropped by at least its threshold. | Inspect the affected evidence and draft a correction proposal. |
| `overall_regression` | The weighted score dropped by at least its threshold. | Treat as a release-blocking signal until reviewed. |
| `correction_regression` | A proposed correction is worse than the baseline beyond the non-regression limit. | Reject or revise the proposal. |
| `overall_correction_regression` | The proposed correction regresses weighted quality. | Reject or revise the proposal. |

Thresholds are explicit fixture/rubric metadata, not hidden evaluator
assumptions. The report preserves every signal; it does not collapse them into
a claim that a prompt is universally good or bad.

## Correction control

Detected drift creates a `proposed` correction record only. The evaluator sets
`auto_promoted` to `false` even when the fixture's corrected score passes the
non-regression comparison. A human reviewer must inspect scope, evidence,
limitations, SemVer impact, and any production evaluation before publishing a
new prompt definition.
