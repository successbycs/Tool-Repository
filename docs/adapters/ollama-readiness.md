# T480 Ollama readiness

`ollama-readiness` is a clean-room, read-only adapter for the local T480
Ollama runtime. It reads only the literal `127.0.0.1:11434/api/tags` inventory
through an explicitly supplied probe and compares it with the digest-pinned
profile set in `catalogue/t480-ollama-model-profiles.json`.

Construct the adapter with `LoopbackOllamaInventoryProbe` only from a process
running on the T480. It has no configurable URL, never submits prompts, and
does not pull, delete, or reconfigure models. `inspect_inventory` reports
`ready: true` only when the installed inventory exactly matches the approved
profile set; an additional, absent, or digest-mismatched model makes it not
ready.

The adapter is local readiness evidence, not a public model API. A remote
solution must not use it as authority to reach the T480 or port 11434.
