# Tool knowledge-base standard

Each adapter links to one `.json` knowledge record through its canonical
descriptor. The knowledge file must name the exact adapter ID and version of
the descriptor that references it. The knowledge base answers two different
questions without blending them:

- **Validated usage** is a dated, bounded observation. It records the adapter
  version, generic context, outcome, constraint or lesson, and an inspectable
  repository evidence reference. It does not prove provider behaviour outside
  that context.
- **Suggested use** is a candidate application. It names assumptions and the
  validation still needed. It must not contain observed outcomes, dates, or
  evidence references, because it is not a proven result.

Repository-wide operating knowledge is maintained as indexed documents in
`docs/`. The [catalogue ingestion standard](catalogue_ingestion.md) defines
how approved adapter, local-model, prompt, and harvested-asset knowledge
becomes catalogue data without treating generated JSON as an editable source.

The JSON contract is `schemas/knowledge-record.schema.json`. Validate the
repository with:

```bash
PYTHONPATH=src python3 -m tool_repository validate --require-knowledge
```

During this baseline phase the command validates the safe fixture when no real
adapter descriptor exists. Once adapters are added, it resolves each
descriptor’s `documentation.knowledge_base` path instead.

Do not include credentials, raw prompts, customer identifiers, raw logs, or
unsupported performance claims. Each validated-use record includes a
`sanitized_repository_evidence` redaction attestation and reviewer identity.
Automated validation catches common credential literals and unsafe paths, but
cannot prove text has no customer data. Admission review is therefore required:
use concise repository-local sanitized test/proof evidence, retain protected
customer evidence outside this library, and record only a safely generalised
lesson here.
