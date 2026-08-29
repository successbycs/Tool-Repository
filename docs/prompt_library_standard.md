# Prompt library and execution provenance standard

## Purpose

Reusable major prompts for intake, assessment, planning, implementation,
review, QA, and remediation are versioned assets. A definition states its
purpose, owner, data classification, input/output contract, constraints, and
static template. An execution record is only privacy-safe provenance; it is
not a transcript, a central execution log, or proof that a milestone passed.

## Definition contract

Store one JSON definition per immutable ID/version under `prompts/definitions`.
Validate it with:

```bash
PYTHONPATH=src python3 -m tool_repository prompts validate
```

A breaking change to purpose, input/output contract, constraints, or expected
behaviour uses a new major version. A compatible capability uses a minor
version; a correction uses a patch version. Definitions name an accountable
owner and a data classification. The checked-in template must never contain a
credential, token, customer content, or hidden reasoning.

## Execution provenance contract

The optional `prompt-execution` record retains only:

- stable execution ID and timestamp;
- prompt ID, version, and SHA-256 of the exact definition bytes;
- bounded milestone/solution context reference;
- provider, model, and named settings profile;
- redacted or protected input/output references with canonical SHA-256 values;
- a status plus evidence hash; and
- the `no_secrets_or_private_content` redaction attestation.

It deliberately has no fields for rendered prompts, raw inputs, raw outputs,
messages, credentials, or reasoning. A protected reference points to the
owning solution's approved system; this repository does not host the content.
The record remains auditable because its immutable prompt version, input/output
fingerprints, context, runtime, timestamp, and outcome can be compared without
copying private material.

Validate an execution record against the checked-in library:

```bash
PYTHONPATH=src python3 -m tool_repository prompts validate \
  --execution path/to/redacted-execution.json
```

## Ownership and promotion

The Tool Repository owns reusable definitions. A solution owns its execution
records and protected references. A reusable prompt improvement must preserve
the source definition ID/version/hash, explain its change and SemVer impact,
add or update non-sensitive tests/evaluation evidence, and be reviewed before
publication as a new immutable definition version.

Do not treat a successful prompt execution as adapter admission, a security
approval, or milestone closure. Those outcomes still require their declared
tests, review, and proof records.
