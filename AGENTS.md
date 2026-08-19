# Tool Repository executor instructions

## Milestone hand-off: mandatory review triad

After every material milestone or iteration update, present a **Review Triad**
table in the chat before the hand-off. This is required whether the milestone
is complete, in progress, blocked, or awaiting review.

Use exactly these rows, in this order:

| Review role | Required | Status | Evidence | Finding / next action |
| --- | --- | --- | --- | --- |
| AI Engineer | yes / no | passed / pending / failed / not required | proof or review link, or `—` | concise factual result |
| Solution Architect | yes / no | passed / pending / failed / not required | proof or review link, or `—` | concise factual result |
| Senior Developer | yes / no | passed / pending / failed / not required | proof or review link, or `—` | concise factual result |

Requirements:

- Derive **Required** from `milestone_registry.json`; never invent a passed review or substitute a plan for evidence.
- Link the saved review record or milestone proof when one exists.
- State `pending`, `failed`, or `not required` plainly. Explain the smallest next action for anything not passed.
- The table reports review state; it does not replace verification, proof, or the milestone close-check.
- Keep normal progress commentary short. The table is required in the final milestone/iteration hand-off, not after every shell command.
