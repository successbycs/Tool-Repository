# T480 lab readiness

`t480-lab` is a clean-room, read-only adapter for a fixed CS AI Lab target.
It reports only six readiness checks: WSL, Docker, storage, Ollama, PostgreSQL,
and n8n.

The consumer provides a `LabRuntimeProbe` that implements the reviewed fixed
inspection for its own transport. The adapter itself never opens SSH, starts a
container, changes a service, reads credentials, or accepts a command string.

Use `inspect_runtime` before a solution performs its separately authorised
operation. A missing probe returns `transport_not_configured`; a malformed
probe result is rejected. A successful local conformance test is not evidence
that the T480 is online.
