# Milestone review triad

The review triad makes milestone confidence visible in the delivery chat. It is a communication control, not a substitute for stored proof, review records, tests, or the close-check.

Use this table after every material milestone or iteration hand-off:

| Review role | Required | Status | Evidence | Finding / next action |
| --- | --- | --- | --- | --- |
| AI Engineer | yes / no | passed / pending / failed / not required | review or proof link | factual result |
| Solution Architect | yes / no | passed / pending / failed / not required | review or proof link | factual result |
| Senior Developer | yes / no | passed / pending / failed / not required | review or proof link | factual result |

`Required` comes from the milestone registry. `Status` is only `passed`, `pending`, `failed`, or `not required`. A role that is not required must still appear, preventing a missing review from being mistaken for a passed review.

For a blocked or in-progress milestone, the final column names the smallest next action. For a completed milestone it states the closure finding and links the durable review record. The executor instructions in `AGENTS.md` make this chat hand-off mandatory for Codex work in this repository.
