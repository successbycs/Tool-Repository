# Milestone execution

## Purpose

This is the operating contract for `milestone_registry.json`. It is derived from AF's useful transition-contract and prompt-capture practices, without making this repository dependent on AF.

The registry declares intended delivery. Verification and proof determine the truthful outcome.

## Source of truth

| Concern | Source |
| --- | --- |
| planned work, dependencies, status, verification | `milestone_registry.json` |
| execution rules and closure requirements | `docs/policies/milestone-policy.md` |
| adapter and release requirements | `docs/policies/adapter-admission-policy.md`, `docs/policies/release-and-change-policy.md` |
| what happened | `runs/proofs/<milestone-id>_*.json` and command/test output |
| durable design decisions | `docs/decision_log.md` |

## Required milestone contract

Every new or materially changed milestone must declare:

- stable `id`, concise `title`, and `delivery_type`;
- the capability that becomes true when it succeeds;
- `dependencies` and an explicit `status`;
- required artifacts and a single `proof_artifact` path;
- reproducible `verify` commands;
- an ingestion assessment: `not_applicable`, or the relevant asset type,
  source records, validation, and catalogue effect defined by
  `catalogue_ingestion.md`;
- an execution brief: objective, relevant context, non-goals, required outputs, proof requirements, verification commands, and stop conditions;
- write scope or a clear statement that no repository files may change;
- for high-risk work, the owner, safety boundaries, and required review.

Milestone implementation may add fields, but must not replace these with vague narrative.

## Status transitions

`not_started` → `in_progress` → `complete` is the normal path. `blocked` may be entered from `not_started` or `in_progress`.

- **not_started:** the work has not begun. Dependencies may still be incomplete.
- **in_progress:** dependencies are complete, scope and stop conditions are understood, and work has started.
- **blocked:** the executor cannot make safe, meaningful progress. Record the blocker, evidence, attempts made, and the smallest next action that could unblock it.
- **complete:** all declared artifacts exist, every verification command has passed in the relevant environment, and the proof artifact records the observed result. Documentation alone is never sufficient proof.

Do not change a milestone to `complete` because code was written, a prompt was sent, or a plan looks plausible. Failed verification returns the milestone to `in_progress` or `blocked` with the failure evidence retained.

## Execution sequence

1. Read the milestone, its dependencies, the applicable policies, and prior related proofs.
2. Check that dependencies are actually `complete` and their proof remains relevant.
3. Write or validate the execution brief and ingestion assessment. When tool
   ingestion applies, follow `catalogue_ingestion.md` before changing source
   records or generated catalogue data. State what will not be changed.
4. Execute within the allowed scope. Preserve major rendered prompts and tool versions according to the prompt-data policy.
5. Run the declared verification commands. Do not substitute a similar command without recording the reason and updating the milestone.
6. Write the proof artifact with commands, results, changed artifacts, and observable evidence.
7. Run the policy/registry validator and required review. Only then transition the milestone.
8. In the final milestone or iteration hand-off, show the review triad in the chat using `docs/milestone_review_triad.md`. Include all three roles even when one is not required or has not yet passed, and give a clear summary of each reviewer's finding or advice.

## Proof standard

A proof artifact must identify the milestone, implementation revision, execution time, environment, exact verification commands, exit results, output hashes, generated artifacts, and the observed result. It must record each required review when the milestone declares one. For a claim about an external system, it must include an inspectable readback or a truthful blocker; a local JSON summary alone is not evidence of an external effect.

## Prompt and review evidence

For a major prompt that informs assessment, planning, implementation, review, QA, or remediation, retain the prompt version/hash, redacted rendered prompt or protected reference, input/output references, model/runtime, and outcome. Prompt capture supports auditability; it never substitutes for verification.

Use the three reviews required by `PROMPT.md` for material design/build work. Review findings must be linked to the milestone proof and either resolved or explicitly deferred with a reason.
