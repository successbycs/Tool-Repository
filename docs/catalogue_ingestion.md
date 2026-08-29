# Catalogue ingestion standard

The read-only catalogue is generated evidence, not an editable inventory.
Never edit `catalogue/adapters.json` directly. Ingest an approved source record,
validate it, and rebuild the catalogue so each published entry is traceable to
immutable source bytes or an exact local runtime observation.

## Required flow

```text
candidate asset
  -> provenance, safety, ownership, and scope review
  -> versioned source record
  -> tests and validation
  -> immutable release reference or exact local digest
  -> catalogue build and validation
  -> generated read-only catalogue
```

Every milestone must declare whether it involves tool ingestion. When it does,
its registry record must name the asset type, source records, required
validation, and catalogue effect. The milestone cannot close without proof of
the declared ingestion path.

## Adapter ingestion

1. Complete read-only intake and record provenance; use a clean-room wrapper
   or owned fork for an external source.
2. Add the canonical `adapter.json`, guide, adapter-specific knowledge record,
   and isolated tests.
3. Bind the immutable tag, full commit, artifact URI, trusted publisher, and
   descriptor SHA-256 in `catalogue/release-index.json`.
4. Run descriptor, contract, and catalogue checks, then generate the catalogue.

## T480 local-model ingestion

1. Obtain authorisation to install or update the model on the T480.
2. Read Ollama's loopback-only `/api/tags` inventory; a mutable tag is not
   sufficient identity.
3. Record the full digest, byte size, parameters, quantisation, role,
   modalities, and limitations in `catalogue/t480-ollama-model-profiles.json`.
4. Require `local_only: true`; do not publish a host, public port, or prompt
   execution operation.
5. Run `python3 scripts/verify_t480_ollama_profiles.py`, build, test, and
   record the local readback in milestone proof.

## Prompts and harvested assets

Prompts first enter the prompt library with a stable ID, version, contract,
owner, constraints, and privacy-safe provenance. Harvested assets remain
candidates until intake establishes licence, provenance, safety, ownership,
and an approved destination. Neither becomes a current adapter-catalogue entry
without a dedicated approved discovery contract.

## Required catalogue commands

```bash
PYTHONPATH=src python3 -m tool_repository catalogue build
PYTHONPATH=src python3 -m tool_repository catalogue validate
```

Commit source records, generated output, proof, and reviews together. The
catalogue never stores secrets, customer data, host configuration, execution
results, or an execution endpoint.
