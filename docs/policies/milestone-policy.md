# Milestone policy

**Version:** 0.2.0  
**Owner:** Tool Repository maintainers  
**Review:** before the first release and whenever the delivery model changes  
**Enforcement:** `schemas/milestone.schema.json` and milestone/policy validators delivered by `TR-M00`

## Rules

1. `milestone_registry.json` is the canonical plan. IDs are stable and never silently reused.
2. Only `not_started`, `in_progress`, `blocked`, and `complete` are valid states.
3. A milestone cannot start while an unmet dependency is not `complete`.
4. `complete` requires all declared verification commands to pass and an inspectable proof artifact that records the actual result, environment, and command-output hashes.
5. `blocked` requires a blocker statement, evidence, attempted actions, and a proposed next action. A blocker is not a successful delivery.
6. Changes to scope, dependencies, or verification must be recorded in the registry and decision log before completion.
7. External-system claims require live readback evidence or a truthful, evidenced failure state.
8. Major prompts and design reviews are execution evidence, not completion evidence.
9. Every material milestone or iteration hand-off in the delivery chat must show the three-row review triad from `docs/milestone_review_triad.md`. It must show required, passed, pending, failed, and not-required states truthfully. The table communicates review state; it never substitutes for proof or the closure check.

## Closure check

The validator must reject closure when dependencies, proof artifact, declared artifacts, required reviews, required verification records, or a dependency cycle are missing. A failing check keeps the milestone `in_progress` or `blocked`.

## Chat hand-off

`AGENTS.md` is the executor instruction that makes review-triad presentation a mandatory Codex hand-off behaviour. The policy validator checks that the instruction and table template exist. It cannot inspect an external chat after the fact, so a reviewer should treat an omitted table as a hand-off defect and request it before accepting the update.
