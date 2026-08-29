# Local Repository Adapter Harvest Map

**Assessment date:** 2026-08-29  
**Scope:** local Git repositories under `/home/chris/projects` and
`/home/chris/SuccessByCS-Builder`.  
**Purpose:** identify integration code that could become a governed Tool
Repository adapter. This is an assessment only: it neither copies source code
nor registers or deploys an adapter.

## How to read this map

- **Clean-room candidate** — valuable, bounded integration behavior that should
  be reimplemented behind the Tool Repository contract, with source provenance
  recorded first.
- **Reference only** — useful implementation or test pattern, but not a direct
  fit for this repository or already covered elsewhere.
- **Defer / do not harvest** — product-domain code, an incomplete repository,
  or a protected external action that should remain where it is.

Any future adoption must have an explicit provenance decision, manifest,
knowledge record, contract tests, and a least-privilege operation set. Local
configuration, credentials, customer data, media, and proof artefacts are
outside the harvesting scope.

## Recommended harvest queue

| Priority | Proposed adapter / component | Best local evidence | Recommendation |
| --- | --- | --- | --- |
| 1 | `t480-transport` | `cs-ai-lab-infra/t480_core/core.py` | **In progress as TR-M05.** Keep only strict target validation and fixed-operation transport; never expose a general remote shell. |
| 1 | `t480-lab` health and readiness bundle | `cs-ai-lab-infra/scripts/t480_adapter.py` | **In progress as TR-M05.** Separate Docker, WSL, service, and storage checks from application actions. |
| 1 | `mp4-transcription-t480` | `mp4-to-transcript/scripts/t480_adapter.py` and its command catalogue | **In progress as TR-M05.** Preserve the private-media and explicit-approval boundary. |
| 2 | `n8n-control-plane` | `cs-ai-lab-infra/scripts/n8n_adapter.py`, AF `scripts/tool_adapters/n8n_adapter.py`, and `vendor-value/src/app/integrations/n8n_client.py` | **Clean-room candidate.** Start read-only: readiness, workflow lookup, and webhook contract validation. Put import, activation, and execution behind explicit protected actions. |
| 2 | `postgres-pgvector-lab` | `cs-ai-lab-infra/scripts/postgres_pgvector_adapter.py` | **Clean-room candidate.** Start with preflight, database/extension inspection, and vector probe. Migration apply must be a separately approved operation. |
| 2 | `ollama-readiness` | `cs-ai-lab-infra/ollama/` and `CSP-Directory/scripts/check_ollama_models.py` | **In progress as TR-M15.** Model listing and exact-digest readiness only; no model pull or runtime reconfiguration. |
| 3 | `vendor-discovery` | `AI_CustomerSuccess/services/discovery/` and `CSP-Directory/services/discovery/` | **Clean-room candidate.** Split provider-specific search from deterministic candidate normalisation, rate limits, and domain filtering. |
| 3 | `web-page-fetch` | `AI_CustomerSuccess/services/enrichment/vendor_fetcher.py` | **Clean-room candidate.** A small, policy-bound HTTP fetcher with timeouts, redirect limits, allow/deny rules, and provenance output. |
| 3 | `ats-job-board-reader` | `leads/controller/ats.py` | **Clean-room candidate.** Read public Greenhouse, Lever, and Ashby boards only; normalise jobs without lead scoring or persistence. |
| 3 | `supabase-diagnostics` | AF `scripts/tool_adapters/supabase_adapter.py` and the directory persistence clients | **Reference for a clean-room candidate.** Limit the first Tool Repository version to configuration/readiness/schema readback; table CRUD and DDL are protected extensions. |
| 3 | `google-sheets-export` | `AI_CustomerSuccess/services/export/google_sheets.py` | **Clean-room candidate.** Caller supplies the row schema; app-specific vendor columns stay in the source repository. |
| 4 | `apify-run-reader` | `AI_CustomerSuccess/services/discovery/apify_sources.py` and `vendor-value/src/app/services/apify_rehydration.py` | **Candidate after vendor discovery.** Read completed run datasets and normalise them; actor execution is credentialed, spend-bearing, and must be opt-in. |
| 4 | `cloudflare-r2-catalogue-publisher` | AF `cloudflare_adapter.py` is a configuration reference only | **New build, not harvest.** AF has no R2 or Workers deployment support. Build the publisher specifically for immutable catalogue objects and least-privilege CI credentials. |

## Repository-by-repository map

| Local repository | Integration seams found | Harvest disposition | Notes |
| --- | --- | --- | --- |
| `SuccessByCS-Builder` | Parent workspace containing Autonomous-Framework and runtime demos. | Reference only | It is an umbrella workspace, not a single adapter implementation. Review the Autonomous-Framework row for the usable surfaces. |
| `SuccessByCS-Builder/Autonomous-Framework` | Cloudflare, Vercel, n8n, Supabase, GitHub, Playwright, Windows/WSL, UiPath, Expo EAS, SQLite, document readers, YouTube, observability, and other scripts under `scripts/tool_adapters/`. Most have matching tests. | Reference only; selectively clean-room rebuild | This is the largest source of patterns, but its CLI scripts have a different runtime and governance model. Do not bulk-copy it. Cloudflare is read-only and does **not** implement R2/Workers publishing. |
| `SuccessByCS-Builder/agent-task-workbench` | TaskBounty task-access and submission protocol. | Defer | Marketplace access, repository forks, pull requests, payments, and submissions are externally binding; retain the human-gate model instead of adding it to the general catalogue. |
| `AI_CustomerSuccess` | Apify search/rendering, generic web search, homepage fetching, OpenAI extraction, Supabase persistence, Google Sheets export, scheduler, local tool specs for n8n/Supabase. | Clean-room candidates | Best source for `vendor-discovery`, `web-page-fetch`, and `google-sheets-export`. Its extraction rules, schemas, and pipeline orchestration are product-specific. |
| `CSP-Directory` | The vendor pipeline plus n8n workflow/webhook client, Supabase, Apify, G2/RapidAPI, Tracxn, Trustpilot, LinkedIn, Google discovery, Ollama checks, and Vercel lead capture. | Selective clean-room candidates | Duplicates much of AI_CustomerSuccess but adds rich n8n workflow patterns. Provider-specific enrichment is spend- and terms-sensitive, so adopt only after a source/provider contract exists. |
| `GEO` | No tracked implementation files found. | Do not harvest | There is no code surface to assess. |
| `Options` | Architecture and product documents only. | Do not harvest | No implementation adapter exists. |
| `OptionsDecisionAgent` | Barchart candidate import/normalisation, sandbox Interactive Brokers Client Portal submission, local T480 health dependency, options-learning-KB read path. | Defer / do not harvest | Financial workflows are high risk. The IBKR integration is intentionally sandbox-only but should remain product-scoped. Barchart normalisation can later inform a generic CSV-normalisation utility, not a trading adapter. |
| `ShamathaTimer` | Expo/React Native release configuration and store-proof tooling. | Reference only | AF already contains an Expo EAS adapter reference. This app has no general-purpose provider client to extract. |
| `Tradify_KB` | Vercel/Next.js routes, Supabase/OpenAI RAG, n8n control surfaces, Cloudflare DNS operating evidence, product-specific `answerops-v1-adapter.ts`. | Reference only | The RAG, approval, and proof routes belong to the KB product. Use its Vercel/Cloudflare deployment evidence to shape future readback contracts, not to extract the application adapter. |
| `barbers` | Static web application with Vercel analytics dependency. | Do not harvest | No reusable backend or provider adapter was found. |
| `cs-ai-lab-infra` | Strict T480 transport, T480 fixed operations, n8n control-plane, PostgreSQL/pgvector adapter, Docker/WSL/Ollama runtime conventions. | Clean-room candidates | Primary source for the current T480 migration. Also the strongest source for subsequent n8n, pgvector, and Ollama readiness adapters. Do not bring over arbitrary remote execution or local infrastructure configuration. |
| `cs-revenue-accelerator` | Vercel serverless lead endpoint, Tally intake, n8n retention-checkup workflows, HubSpot/WhatsApp links, static marketing site. | Reference only | The Vercel API and form workflow are product-specific. The n8n workflow files may provide test fixtures for the future `n8n-control-plane` adapter. |
| `forex` | Fixed T480 health/MetaTrader process operations and evidence validation. | Defer | The T480 health pattern overlaps the lab adapter. Forex/MetaTrader operations must remain isolated from a generic Tool Repository due to financial risk. |
| `leads` | Search backend abstraction (Google Custom Search and SerpApi), public ATS readers (Greenhouse, Lever, Ashby), Reddit, NewsAPI, RapidAPI company posts, SQLite exports, n8n workflow definitions. | Clean-room candidates | Best source for a bounded `ats-job-board-reader` and a pluggable `web-search` interface. Lead scoring, contact prioritisation, and source persistence are product-specific. |
| `mp4-to-transcript` | T480 application adapter, fixed transcription preflight/runtime checks, Docker one-shot worker, private local media handling. | Clean-room candidate | Current TR-M05 source for `mp4-transcription-t480`. Do not turn it into a cloud-media or generic file-execution service. |
| `options-learning-kb` | T480 application adapter, read-only source-cited retrieval API, PostgreSQL/pgvector and Ollama readiness dependency. | Candidate after M05 | The reusable part is an application-specific read-only health/readiness contract. Its transcript, source approval, embeddings, and retrieval domain stay in this repository. |
| `revenue-fix-engine` | Vercel early-access email route, Google SMTP, HubSpot and WhatsApp page integrations. | Do not harvest | It duplicates the marketing-site pattern and has no governed general-purpose adapter surface. Email delivery should be assessed separately with a secure provider and consent model. |
| `vendor-value` | n8n client and callback contract, n8n workflow assets, Apify workbook rehydration, internal FastAPI pipeline. | Clean-room candidates | Good reference for a typed `n8n-control-plane` client and for a local workbook input contract. Its evidence/review/publish pipeline is product-specific. |

## Existing sources worth using only as references

These sources contain implementation value but should not be treated as
drop-in Tool Repository modules:

1. **AF Cloudflare adapter** — token/account/zone verification and zone
   listing only. It has no R2 bucket, object, Worker, or deployment operation.
2. **AF Vercel adapter** — a useful control-plane/readback pattern, while the
   catalogue architecture is intentionally moving to Cloudflare R2 plus a
   Worker rather than Vercel.
3. **AF Windows/WSL bridge** — its staging and arbitrary PowerShell capability
   is broader than the Tool Repository safety model. Retain only strict,
   fixed-operation concepts in the T480 transport adapter.
4. **Application `t480_adapter.py` files** — application command catalogues
   should become separate adapters, not one large multi-purpose remote-control
   adapter.

## Recommended delivery sequence

1. **Complete TR-M05:** finish and prove the three currently authorised T480
   adapters before admitting further source material.
2. **Complete TR-M01A, then TR-M04:** the existing roadmap requires a
   deployable immutable release before the generated catalogue and read-only
   API can be exposed. Publish catalogue JSON to private R2 through CI and
   expose it through a Worker. This is a new implementation, not a harvest.
3. **Use existing TR-M06:** demonstrate a solution consuming one pinned,
   approved adapter from the catalogue and contributing a safe local change.
4. **Register new, separately scoped adapter milestones:** first
   `n8n-control-plane`, then `postgres-pgvector-lab` plus `ollama-readiness`,
   then research connectors (page fetch, search, ATS, and optional Apify
   completed-run reads). These milestones do not yet have registry IDs.
5. **Later optional work:** Google Sheets export and Supabase diagnostics,
   each using a caller-owned schema rather than application tables embedded in
   an adapter.

## Explicit exclusions

- Financial execution, brokerage, MetaTrader, and trading recommendation
  workflows.
- General remote shell, arbitrary PowerShell, arbitrary SQL, or unbounded file
  transfer.
- Product-specific scoring, customer data models, RAG logic, credentials,
  workflow secrets, media, local `.env` files, and historical proof artefacts.
- Direct source copying without a recorded provenance decision and review.

## Evidence reviewed

The detailed source locations are the local repository paths named in the
tables. Key implementation references include:

- `/home/chris/projects/cs-ai-lab-infra/scripts/t480_adapter.py`
- `/home/chris/projects/cs-ai-lab-infra/scripts/n8n_adapter.py`
- `/home/chris/projects/cs-ai-lab-infra/scripts/postgres_pgvector_adapter.py`
- `/home/chris/projects/AI_CustomerSuccess/services/discovery/apify_sources.py`
- `/home/chris/projects/AI_CustomerSuccess/services/enrichment/vendor_fetcher.py`
- `/home/chris/projects/leads/controller/ats.py`
- `/home/chris/projects/vendor-value/src/app/integrations/n8n_client.py`
- `/home/chris/SuccessByCS-Builder/Autonomous-Framework/scripts/tool_adapters/`
