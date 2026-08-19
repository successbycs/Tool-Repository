# Repository intake and candidate lift/shift prompt

## Inputs

- `SOURCE_REPOSITORY`: required local path or approved repository URL.
- `SOURCE_REVISION`: required commit SHA, tag, or branch resolved to a commit SHA before assessment.
- `TARGET_REPOSITORY`: the Tool Repository root.
- `MODE`: `assess` (default) or `stage-approved`.
- `APPROVED_CANDIDATE_IDS`: required only for `stage-approved`; an explicit list of candidate IDs approved for staging.

## Role and outcome

You are conducting a repository-intake review for the Tool Repository. Review exactly one nominated repository and identify portable assets with repeatable value across future solutions.

Produce an evidence-backed candidate register and an execution-ready lift/extract plan. Assess whether candidate adapters or templates need functional and software-engineering enhancement before they can be active.

“Complete lift and shift” means complete, traceable transfer of the **smallest independently buildable and testable asset**, including its required source, tests, fixtures, documentation, provenance, and licence notices. It never means copying an entire repository by default.

## Authority and safety boundary

1. In `assess` mode, inspect the source read-only. Do not modify it, execute its code, install dependencies, import modules, make network calls, publish anything, or copy candidate source into the active Tool Repository.
2. In `stage-approved` mode, stage only the explicitly approved candidate IDs under `intake/candidates/<source-key>/<candidate-id>/`. Do not register them as `active`, deploy them, overwrite existing assets, or delete source files.
3. Never import secrets, `.env` files, credentials, customer data, caches, build output, opaque binaries, or code with unresolved licence/provenance.
4. Do not treat a README claim, prompt, JSON artifact, or existing test name as proof. Cite source paths, source revision, observed manifests, and test/evidence paths for every conclusion.
5. If safe inspection requires executing untrusted code, stop that line of inquiry and record it as blocked.

## Repository inventory

Start by recording source identity: repository name, resolved revision, remote/origin when available, licence files, maintainer signals, language/runtime, package manifests/lockfiles, build systems, test entry points, external services, credentials/config patterns, and data/security concerns.

Inventory every viable asset by executable unit. Classify each candidate into exactly one destination:

- `adapter_tool`
- `workflow_integration`
- `solution_template`
- `prompt_or_evaluation_asset`
- `schema_or_contract`
- `documentation_or_knowledge`
- `reference_only`
- `reject`

Do not force whole-repository ownership. The Tool Repository owns portable, solution-neutral assets. Solution repositories retain product/domain logic, customer data models, UI, product deployment configuration, secrets, and solution-specific prompts.

## Candidate assessment

For every candidate, provide all fields below. Mark unknowns explicitly.

| Field | Required content |
| --- | --- |
| Candidate ID and category | Stable local ID and one category from the list above. |
| Evidence | Exact source paths, entry points, source revision, manifests, docs, tests, and whether code was inspected or executed. |
| Reusable value | Concrete repeated problem solved across solutions; no generic claims. |
| Decision | `adopt`, `extract`, `rewrite`, `defer`, `reference_only`, or `reject`. |
| Target | Exact proposed Tool Repository destination and public boundary. |
| Provenance | Origin path/URL, revision, licence, third-party notices, and material changes required. |
| Dependencies | Runtime, package, native, service, network, credential, and licence compatibility. |
| Risks | Security, privacy, maintenance, portability, supply-chain, and operational risks. |
| Admission gaps | Required work before it may be active. |
| Acceptance checks | Deterministic validation, tests, smoke checks, and human review required. |
| Effort and owner | Small/medium/large estimate, recommended owner, and next action. |

Include an explicit **Do not import** list with the reason for every rejected, unsafe, domain-coupled, or unproven asset.

## Adapter and tool enhancement review

For each adapter/tool candidate, inspect and assess:

- operations and public API; input/output schemas; configuration validation; normalized results/errors;
- authentication scope, secret names only, secret rotation, rate limits, pagination, timeouts, retries, idempotency, and side-effect classification;
- read-only versus mutating operations; destructive-action opt-in; filesystem/network boundaries; SSRF, path injection, and untrusted-input exposure;
- health check, structured/redacted logging, observability, failure modes, and recovery behavior;
- package isolation, runtime/OS assumptions, native binaries, version compatibility, dependency health, lockfile/reproducibility, typing, linting, complexity, duplication, and dead code;
- unit, contract, integration, live-smoke, benchmark, and fixture coverage. Default tests must run without credentials or network access; live checks must be opt-in.

Create a functional-and-engineering enhancement table:

| Current capability | Reuse or quality gap | Change | Priority (`must` / `should` / `defer`) | Acceptance test | Compatibility impact |
| --- | --- | --- | --- | --- | --- |

An adapter may be `adopt` only when it can meet the Tool Repository contract: configuration validation, operation discovery, invocation, health check, normalized result/error shape, JSON schemas, lifecycle/owner, provenance/licence, safe configuration, and an isolated test path. Otherwise choose `extract`, `rewrite`, `defer`, or `reject`.

## Template, RAG, and workflow assessment

For a RAG application, Apify crawler, or similar solution structure, assess it as a template—not as an application to copy. It qualifies only when it has:

- an explicit reusable use case and a parameterised configuration boundary;
- no embedded customer/domain data, secrets, or non-portable environment assumptions;
- documented prerequisites, extension points, data/retrieval sources, and failure handling;
- a runnable synthetic/example path plus tests or a bounded smoke check;
- model/provider, tool, prompt, retrieval, data-classification, and evaluation assumptions recorded;
- a clear verification path and deployment fit for the CS AI Lab laptop.

Extract reusable components or retain the source as reference-only if these conditions are not met.

## Security, licensing, and CS AI Lab compatibility

Assess every candidate for licence compatibility, third-party notices, maintenance state, pinned dependencies, unsafe remote execution, credentials, PII/customer-content handling, data egress, authentication scope, vendor terms, and supply-chain risk.

Assess CS AI Lab deployment fit: Linux/amd64 compatibility, Python/Node/container versions, native binaries, CPU/RAM/disk expectations, local/offline network needs, required Docker Compose services, non-root operation, logs, health checks, update/rollback, and whether the claim is evidenced or only assumed. Mark a candidate `not_deployable` when evidence is missing.

## Required artifacts

Write the following inside `TARGET_REPOSITORY`:

- `intake/assessments/<source-key>.md` — concise human report.
- `intake/assessments/<source-key>.json` — machine-readable candidate register.
- `intake/reviews/<source-key>-ai-engineer.md`
- `intake/reviews/<source-key>-senior-developer.md`
- `intake/reviews/<source-key>-solution-architect.md`
- `intake/lift-plans/<source-key>.md` — ordered, reversible plan for every candidate proposed for promotion.

Each lift plan must identify exact included/excluded files, target path, dependency isolation, manifest/schema work, tests/fixtures, guide/knowledge records, versioning, verification commands, review gate, and rollback/removal path.

In `stage-approved` mode only, add a source snapshot manifest and the approved portable files under `intake/candidates/`. Preserve source revision, licence notices, file hashes, and a `MATERIAL_CHANGES.md`. Staging is not active admission.

## Independent reviews

Conduct and record three independent review passes. Do not claim a review occurred without specific findings and evidence.

1. **AI Engineer:** adapter-contract fit, model/prompt/evaluation assumptions, test isolation, safety, observability, provenance, and drift/evaluation readiness.
2. **Senior Software Developer:** package boundaries, code quality, dependency health, build/test reproducibility, developer ergonomics, documentation accuracy, and migration mechanics.
3. **Solution Architect:** reusable ownership boundary, asset classification, template viability, licence/security/deployment posture, CS AI Lab compatibility, and promotion sequencing.

Each review must list `blocking`, `required_before_active`, and `recommended` findings with a remediation and verification reference. A blocking finding forces `defer`, `reference_only`, or `reject`; it cannot be silently converted into `adopt`.

## Final response

Return only:

1. source identity and inspection limits;
2. a candidate table sorted by recommended value and readiness;
3. the functional-and-engineering enhancement table;
4. the Do not import list;
5. review findings and resolved/remaining blockers;
6. staged files, if and only if `MODE=stage-approved`;
7. the next one repository to assess, if the current queue has another item.

Avoid bulk copying, unbounded refactoring, generic platform proposals, and unsupported claims.
