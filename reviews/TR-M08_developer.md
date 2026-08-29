# TR-M08 Senior Developer review

Passed: the CLI accepts the documented fixture directory, generates a stable
JSON report, detects candidate drift, reports a passing correction comparison,
and rejects incomplete scores, invalid calibration, unknown prompt versions,
and secret literals. Tests also prove a regressing correction remains visible
and is never auto-promoted.

Advice: preserve deterministic report ordering and extend the schema before
adding any new evaluator or correction state.
