# Tool descriptor standard

`adapter.json` is the single source of truth for a reusable adapter release.
The generated catalogue in TR-M04 will read descriptors; maintainers must not
create a second hand-edited registry. Descriptor discovery is static and never
imports adapter code.

The descriptor schema is versioned in `schemas/adapter.schema.json`. The v1
contract requires the following, because each field answers a decision a
solution builder must make:

| Section | Answers |
| --- | --- |
| `adapter` | What is it, which exact SemVer release is it, who owns it, and is it active? |
| `value` | Which use cases fit, which do not, and what limits apply? |
| `provenance` | Where did it originate, at which revision, under which licence, and what changed? |
| `capabilities` / `operations` | What can it do, with which schemas, side effects, idempotency, timeouts, and retry guidance? |
| `configuration` | What configuration shape is required and which secret *names* are needed? Never put a secret value here. |
| `safety` / `health_check` | How data is handled, whether logs redact secrets, destructive opt-in, and a read-only readiness operation. |
| `documentation` | Where the concise user guide and knowledge record live. |

Use `PYTHONPATH=src python3 -m tool_repository validate path/to/adapter.json`
before admission. With no paths, it checks `adapters/**/adapter.json`. The
validator applies the published Draft 2020-12 descriptor schema, meta-validates
embedded input/output/configuration schemas, then applies cross-field safety
rules. It also requires both documentation paths to exist; TR-M03 will validate
the knowledge-record content. A valid descriptor does not itself make an
adapter active: licence/provenance review and conformance tests remain admission
requirements.

## Authoring rules

- Pin a concrete SemVer adapter version and record the contract version.
- Keep `summary`, `fit_for`, `not_for`, and `limitations` specific enough for a
  solution team to choose safely without opening implementation code.
- Use JSON Schema objects for every operation input/output and configuration.
- For configuration fields whose name is a declared secret or looks like a
  credential (`token`, `password`, `api_key`, etc.), never include `default`,
  `const`, examples, or an enum of values in the schema.
- Declare `read_only`, `mutating`, or `destructive` accurately. Destructive
  operations cannot have unknown idempotency and need shared runtime opt-in.
- `documentation` paths are repository-relative. A user guide explains setup
  and one copyable use case; `knowledge_base` must point to a JSON knowledge
  record for the same adapter ID and version, where evidence is recorded
  separately.
