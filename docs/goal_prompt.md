# Goal prompt and approval flow

Use the versioned `goal-definition-and-milestone-seed` prompt to turn a stated
outcome into a **candidate** goal. It captures the desired outcome, bounded
scope, non-goals, success criteria, proof requirements, dependencies, authority
needed, and candidate milestones.

The prompt is not an approval mechanism. A repository owner must review the
candidate and create an approved record under `goals/approved/` that validates
against `schemas/goal-record.schema.json`. Only records whose approval status
is exactly `approved` can enter `catalogue/adapters.json`.

```text
goal prompt
  -> candidate goal (human review)
  -> approved goal record
  -> milestone registry
  -> ingestion / implementation / verification
  -> proof + Review Triad
  -> generated catalogue metadata
```

The generated catalogue is intentionally metadata-only. It shows a goal's ID,
version, title, desired outcome, linked milestones, approval status, and source
hash. It does not contain approval identities, raw prompt inputs or outputs,
hidden reasoning, credentials, customer data, or an execution endpoint.

For this repository, the first approved example is
`goals/approved/tool-repository-goal-flow-1.0.0.json`, which governs TR-M16.
