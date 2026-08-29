# Adapter contract

Every active adapter implements one small synchronous, transport-neutral boundary:

1. `validate_config(config)` returns configuration errors without external work.
2. `list_operations()` returns static operation definitions.
3. `_invoke_operation()` performs one already-authorized operation.
4. `invoke()` is the shared guard: it resolves declared operations, validates configuration and input/output JSON Schemas, and rejects destructive work unless `allow_destructive=True`.
5. `health_check()` is read-only and returns a normalized result.

`AdapterResult` is either a success with object output and no error, or a failure with no output and an error containing `code`, safe `message`, and `retryable`. It must never contain credentials or private data.

The contract is synchronous in v1. Adapters own their transport timeout and retry behaviour; an async interface is intentionally deferred until a real adapter requires it. `TR-M02` adds full manifest and JSON Schema validation before any adapter becomes active.

Admission conformance explicitly compares an imported candidate's runtime operation definitions with its already validated manifest. This is separate from static discovery, which never imports adapter code.
