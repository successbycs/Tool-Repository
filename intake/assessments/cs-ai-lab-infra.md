# CS AI Lab infrastructure intake assessment

## Source and inspection limits

- Source: `/home/chris/projects/cs-ai-lab-infra`
- Revision: `551f1afe972172ba9eee707a81a12072c8473ee0`
- Inspection: static source and a read-only T480 bridge preflight only.
- Licence: no repository licence file found; code cannot be copied or admitted
  until ownership/licensing is recorded or the asset is clean-room rewritten.

## Candidates

| Candidate | Category | Decision | Value and boundary | Required before active |
| --- | --- | --- | --- | --- |
| `t480_wsl_lab` | adapter_tool | extract | Governed T16→T480 Windows→WSL fixed-operation bridge; never a remote shell. | Resolve licence/provenance; separate transport core; map every operation to Tool Repository manifest; fake-transport tests; explicit live-smoke gate. |
| `ollama_local` | adapter_tool | rewrite | Solution-local configured Ollama client; no T480 address, deployment, model storage, or central execution service. | New clean-room implementation; JSON schemas; fake HTTP tests; endpoint/SSRF policy; model and embedding/generation operation contract. |
| `n8n_t480` | workflow_integration | defer | Private loopback n8n control bridge. | Licence and isolated dependency review; follows after T480 transport extraction. |
| `postgres_pgvector_t480` | adapter_tool | defer | Governed pgvector diagnostics and reviewed migration path. | Licence, database safety review, fake transport, and migration-evidence design. |
| `t480_core` | schema_or_contract | reference_only | Useful transport boundary pattern. | Do not copy until its standalone package/provenance are established. |

## Do not import

- `.env`, ignored local target configuration, API-key files, audit logs, raw
  T480 evidence, SSH configuration, and private host output: contain or locate
  credentials/private infrastructure.
- The broad bootstrap prompt and any arbitrary-command compatibility behaviour:
  inconsistent with the Tool Repository fixed-operation safety model.
- Docker/Compose deployment configuration: platform-specific infrastructure,
  not a reusable solution adapter.

## Promotion sequence

1. Record source licence/ownership or explicitly authorize clean-room rewrite.
2. Extract the T480 fixed-operation public contract with a transport seam and
   opt-in live smoke tests; do not copy connection details.
3. Build `ollama_local` independently as a portable HTTP adapter, then test it
   against a fake transport and an opt-in local Ollama smoke target.
4. Promote only after descriptor, guide, knowledge record, conformance tests,
   and three-role review pass.
