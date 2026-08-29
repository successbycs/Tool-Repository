# Repository asset intake

`intake/repository_queue.json` is the source queue. Exactly one source may be
`assessing`; validation is read-only and never imports source modules, executes
source code, installs dependencies, or makes network calls.

Run `PYTHONPATH=src python3 -m tool_repository repositories validate-queue`.
An assessment must bind to the queued source ID and full revision, record
candidate evidence, security posture, admission gaps, acceptance checks, owner,
and effort. Unknown or unresolved licensing prevents `adopt` and `extract`;
such candidates remain `rewrite`, `defer`, `reference_only`, or `reject`.

Assessment is not promotion. Promotion requires its own approved milestone,
descriptor, conformance tests, and review evidence.
