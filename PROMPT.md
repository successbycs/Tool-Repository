# Build the Tool Repository

## Role

You are a senior Python platform engineer building a small, durable developer library. Make deliberate choices, favour deletion over abstraction, and challenge every proposed component. Do not add a feature merely because it could become useful later.

## Context

This repository is the canonical home for reusable integration adapters used by many solution repositories. The local Autonomous Framework (AF) contains candidate adapters and useful patterns, but it is not a dependable runtime and must not become a dependency of this repository or its consumers.

Existing solution work already reuses AF adapters as starting points. This repository formalises that successful workflow:

```text
solution develops or improves an adapter
  -> adapter is made generic, tested, documented, and versioned here
  -> future solutions install a pinned release or intentionally fork it
```

## Product Definition

Build a source-first, versioned **adapter library**. It is not an AI platform, agent framework, orchestration system, plugin marketplace, control plane, or universal tool registry.

Its sole job is to make proven adapters easy to find, understand, test, consume, fork, and contribute back.

AF is only a migration source for adapter candidates and an optional future compatibility target. Do not import, execute, or require AF code. Do not copy its controllers, policies, registries, proofs, or unfinished runtime.

## V1 Decisions — Do Not Expand Them

- Use Python 3.12+ and one package-management/test toolchain already appropriate for the repo. Do not introduce multiple SDKs, runtimes, package managers, or deployment modes.
- Use one small adapter contract.
- Use a per-adapter `adapter.json` manifest as the canonical metadata source.
- Generate the human-readable root catalogue from manifests. Never maintain a second hand-edited registry.
- Make the generated catalogue machine-readable and available through a stable, read-only catalogue/release-resolution interface. It must read allowlisted manifest files and never import or execute arbitrary adapter code.
- A solution consumes an exact released adapter version by default. Copying/forking is allowed only for solution-specific work and must retain provenance.
- Keep adapter-specific dependencies isolated to that adapter.
- Prefer normal package and test commands. Add a small command only where it removes meaningful repetition.

Explicitly exclude from V1: a database, a stateful central control plane, a tool-execution proxy, a web UI, dynamic remote loading, an auto-update agent, a telemetry platform, a marketplace, code-generation framework, generic workflow engine, and AI/LLM requirements.

## Required Repository Contents

Create only the smallest useful structure. A good initial shape is:

```text
src/tool_repository/              # small shared contract, manifest reader, conformance harness
adapters/<adapter-id>/            # source, adapter.json, README, tests, changelog
examples/minimal-solution/        # consumes one exact pinned adapter version
docs/                             # short contribution, lifecycle, and migration guidance
scripts/                          # only if a script removes repeated work
tests/                            # contract/discovery tests
```

Adjust names when a simpler conventional Python layout is better, but do not create empty directories, placeholder systems, or speculative layers.

### Canonical adapter contract

Define a minimal, typed contract that every adapter can meet. A manifest must include:

- stable adapter ID and SemVer version
- adapter-contract/protocol version
- short description and capabilities
- input and output JSON Schemas for each declared operation
- configuration schema and **secret names only** (never secret values)
- side-effect and idempotency classification per operation
- timeout/retry guidance
- lifecycle status: `active`, `deprecated`, or `archived`
- maintainer, license, and provenance: origin repository/path, source revision, origin license, and material changes from origin
- deprecation replacement when applicable

The runtime contract must expose only what is needed for reuse:

1. configuration validation
2. declared operation discovery
3. invocation
4. health check
5. one normalized result/error shape

Do not require MCP. If an adapter supports MCP, that is an implementation detail. Include a very small optional AF compatibility shim only if it can implement AF's `list_tools()`, `invoke()`, and `health_check()` without importing AF.

### Standard tool schema and knowledge base

Create a versioned JSON Schema for the canonical `adapter.json` descriptor and validate every manifest against it. This schema is the common language for people and automation: a reader must be able to tell what a tool is, why it matters, whether it fits their task, and how to use it without opening implementation code.

In addition to the technical contract fields above, require every active adapter descriptor to declare:

- a one-sentence purpose and a short, concrete value statement;
- the problem(s) it solves, expected inputs and outputs, supported systems, and capability tags;
- `when_to_use`, `when_not_to_use`, limitations, prerequisites, and safety/permission boundaries;
- links to its user guide, operation reference, configuration reference, examples, and knowledge-base records;
- a support/lifecycle owner and last-reviewed date.

Each adapter must carry a concise, Markdown knowledge base beside its source. It must include a quick-start guide, configuration and authentication guidance, operation-by-operation examples, expected results, troubleshooting/known limitations, and safe-use notes.

It must also contain two explicitly separate knowledge record types:

- **validated usage records** — evidence-backed accounts of how the adapter was used: date, use-case context, adapter version, outcome, constraints/lessons, and a safe reference to a test, example, or proof artifact. Never include customer data, secrets, or unverified success claims.
- **suggested use cases** — clearly labelled possible future uses, with assumptions and validation still required. These must never be presented as proven usage.

Keep knowledge current through the adapter lifecycle: a change that affects behaviour, configuration, safety, limits, or recommended use must update the guide and relevant record. Require a knowledge-base link and one runnable example before an adapter can be `active`.

### Automated access API

Solutions need a stable way to discover and resolve adapters automatically. Implement this as a read-only catalogue/release-resolution API over the generated manifests, alongside local file and CLI access. It is a discovery API, not a remote adapter-execution gateway.

It must support:

- listing active adapters and their capabilities;
- retrieving one adapter's manifest, schemas, lifecycle, provenance, and compatible versions;
- resolving an exact or SemVer-constrained version to immutable package/artifact coordinates and checksum;
- filtering by capability, lifecycle status, and contract version;
- retrieving the tool's value/use summary and links to its user guide and knowledge-base records;
- returning structured errors for unknown, malformed, or deprecated adapter requests.

Keep it stateless and replaceable: a generated JSON catalogue is the source, and an HTTP delivery layer may be a thin static or read-only wrapper around it. No credentials, solution configuration, adapter invocation, execution logs, or vendor secrets may pass through this API. A solution installs the resolved adapter and invokes it in its own environment.

## Quality and Safety Requirements

- Every adapter is independently usable and contains implementation, manifest, concise README, configuration guidance, contract tests, and a short changelog—nothing more by default.
- Implement a shared conformance suite. An adapter cannot be active unless it passes it.
- Default tests must use fakes/fixtures and must not require credentials, a network connection, or live vendor accounts. Add opt-in live smoke tests only where useful.
- Include negative tests for invalid configuration, authentication failures, schema validation, and normalized error mapping.
- Secrets may be supplied only by environment variables or secret references. Redact them from results and logs.
- Destructive operations must be declared, disabled by default, and require explicit opt-in at invocation.
- Detect duplicate adapter IDs and invalid/deprecated lifecycle declarations. Make invalid manifests fail validation clearly.
- Release artifacts are immutable. Consumers pin exact versions.

## Migration and Initial Scope

Inspect the local Autonomous Framework repository at `/home/chris/SuccessByCS-Builder/Autonomous-Framework` as a candidate source only.

1. Produce a concise migration inventory classifying candidate adapters as `adopt`, `extract`, `rewrite`, `defer`, or `discard`, with one sentence of evidence each.
2. Migrate only two or three high-value, working, broadly reusable adapters. Do not bulk-copy AF's tool registry, scripts, policies, or directory structure.
3. Include one simple reference adapter and one external-service adapter with a fully mocked default test path.
4. Preserve provenance for anything derived from AF.

### Repository asset intake

Create a repository-intake queue and assess exactly one source repository per intake run. Each queue item must name a local path or approved source URL, owner/source, revision, licence/provenance status, and review status. Inspection is read-only by default: do not execute untrusted code, install dependencies, import modules, or copy files into this repository merely because they appear useful.

For each source, produce a concise assessment that classifies each candidate as `adopt`, `extract`, `rewrite`, `defer`, or `reject`. Record the evidence, licence, maintenance signal, security concerns, tests available, integration boundary, proposed destination, and the reason it would create repeatable value across solutions.

Candidates may include adapters, tools, workflow recipes, prompts, evaluation fixtures, data schemas, and reusable solution structures. A solution structure such as a RAG application template or Apify crawler is promoted only when it is a generic, documented, tested starting point—not a copied application. It must have a clear configuration boundary, no embedded secrets/customer data, and a defined verification path. Promotion remains a separate reviewed milestone; assessment is not permission to import code.

## Delivery Milestones

Use the repository's AF-style `milestone_registry.json` as the delivery plan. A milestone registry schedules and proves delivery; it does not replace policy. Create the milestones below with dependencies, a clear capability unblocked, required artifacts, proof artifact paths, and verification commands. Keep them `not_started` until their proof and verify commands genuinely pass.

1. **TR-M00 — Governance Policy Baseline:** establish the small, versioned policy set and executable policy checks that govern milestones, adapters, releases, knowledge, and prompt data.
2. **TR-M01 — Repository Contract Foundation:** establish the minimal package, AF-style milestone registry, shared adapter contract, and validation/test entry points.
3. **TR-M01A — CS AI Lab Deployable Release:** deliver an immutable tagged release and a verified, non-root installation/update/rollback path on the CS AI Lab laptop.
4. **TR-M02 — Standard Tool Descriptor Schema:** implement the versioned JSON Schema, manifest validator, and plain-language descriptor requirements for value, fit, limitations, lifecycle, and documentation links.
5. **TR-M03 — Tool Knowledge Base Contract:** implement the per-adapter guide and knowledge-record format; enforce quick start, configuration, examples, limitations, validated usage records, and clearly labelled suggested uses.
6. **TR-M04 — Machine Discovery and Catalogue API:** generate a catalogue solely from valid manifests and expose its read-only discovery/release-resolution interface, including value/use and knowledge-base links.
7. **TR-M09 — Repository Asset Intake:** assess an explicit queue of source repositories one at a time and create evidence-backed, licence-aware promotion proposals for reusable adapters, workflows, templates, prompts, evaluation assets, and documentation.
8. **TR-M05 — Reference Adapters and AF Extraction:** migrate the selected small set of high-value AF candidates with provenance, complete descriptors, knowledge bases, mocked conformance tests, and opt-in live checks where relevant.
9. **TR-M06 — Solution Consumption and Contribution Loop:** deliver the minimal solution example/template, exact-version resolution, local override/fork provenance, and contribution-back workflow.
10. **TR-M07 — Prompt Library and Execution Provenance:** implement prompt-definition and execution-record schemas with privacy-aware capture and solution-local ownership.
11. **TR-M08 — Prompt Evaluation and Drift Correction:** implement reproducible evaluation fixtures, calibrated drift assessment, static visibility, and evidence-backed correction proposals.

Every milestone must have an observable proof artifact and verification that checks real repository behaviour. A document existing by itself is not proof: schema validation, catalogue generation, discovery response, conformance tests, and runnable examples must demonstrate the claimed capability.

### Policy layer

Create a deliberately small set of versioned policy documents under `docs/policies/`. Each policy states its purpose, scope, owner, version, review date, enforcement points, and change history. Do not create policy documents that cannot name a concrete enforcement point.

- `milestone-policy.md` — allowed statuses (`not_started`, `in_progress`, `blocked`, `complete`), transition criteria, dependency rules, required proof, and truthful closure rules. A milestone may become `complete` only after its declared verification passes and its proof artifact records the observed result.
- `adapter-admission-policy.md` — requirements for active adapters: schema validation, conformance tests, provenance/license, security classification, knowledge base, owner, and release/deprecation rules.
- `knowledge-policy.md` — required guide content, evidence standard for validated usage, labelling of proposed uses, review cadence, and removal/redaction process.
- `prompt-data-policy.md` — prompt ownership, versioning, capture rules, data classification/redaction, execution evidence, retention, and prohibition on storing secrets or hidden reasoning.
- `release-and-change-policy.md` — SemVer, immutable releases, compatibility, changelog expectations, and how policy/schema/adapter changes are proposed, reviewed, and recorded.

Use a short `docs/policies/README.md` as the policy index. Enforce policy through validators and CI wherever possible: for example, fail active adapters without a knowledge-base link, reject milestone completion without passing verify commands and a proof artifact, and reject manifests that violate the admission policy. Policy changes must update the relevant policy version and add an entry to `docs/decision_log.md`; they must not silently alter historical execution records.

## Developer Experience

Optimise for a developer creating a new solution. In under five minutes, they must be able to find an adapter, understand configuration and capabilities, run tests, and consume it—or deliberately fork it.

Document these simple workflows with copyable commands:

- discover/list adapters and their capabilities
- resolve a pinned adapter automatically through the local and read-only catalogue API
- validate every manifest
- run all contract tests and a single adapter's tests
- create a new adapter from the minimal scaffold
- consume a pinned adapter in a solution
- fork an adapter while recording `derived_from`, source version, and material changes
- promote a solution adapter back into this repository

The scaffold and contribution path must be lightweight: generalise the adapter, pass conformance tests, add/update manifest and README, record provenance and changelog, version it, and submit it. No approval workflow, framework integration, or central runtime is required to use an adapter.

## Solution Template

Include a minimal solution-facing template/example that:

- declares exact adapter pins
- validates local configuration
- includes adapter contract tests or invokes the shared suite
- documents local override/forking and contribution-back instructions
- does **not** create a second solution-local registry or require AF

## Prompt Library and Drift Visibility

Major prompts that advance a solution—intake, assessment, planning, implementation, review, QA, and remediation—must be versioned governed assets. Reusable prompt definitions belong here; rendered solution-specific executions remain in the solution repository unless a redacted generalisation is promoted.

Define versioned schemas for a prompt definition, execution record, and evaluation record. Capture the exact rendered prompt only when its data classification permits; otherwise capture a redacted form, hash, input fingerprint, and protected reference. Never store secrets, private customer data, or hidden reasoning.

Assess execution against an explicit contract, not subjective prose similarity. Start with deterministic checks for required outputs/evidence, output schema, allowed tools and versions, scope, stop conditions, and verification results. Then record rubric findings for objective fulfilment, grounding, safety, and usefulness.

Classify drift as `objective_drift`, `scope_drift`, `constraint_drift`, `format_drift`, `evidence_drift`, `tool_drift`, `grounding_drift`, or `context_drift`. Report a scorecard of separate measures—contract pass rate, evidence coverage, schema pass rate, drift rate by type, review pass rate, rework rate, cost, and latency—rather than one opaque score.

Provide machine-readable records and a generated static report/CLI query. Drift must produce a versioned correction proposal linked to the failed execution. Do not silently change a prompt or promote a new version without comparable evaluation evidence.

## Acceptance Criteria

The implementation is complete only when all of the following are demonstrably true:

1. A clean checkout validates all manifests and runs all default tests without credentials or network access.
2. A developer can discover an adapter from the generated catalogue and install/use a documented pinned version.
3. The reference adapter and external-service adapter both pass the shared conformance suite.
4. A new adapter can be scaffolded, made valid, and tested with the documented workflow.
5. The minimal solution example uses a pinned adapter and explains a local override.
6. A malformed manifest and an unapproved/destructive invocation are rejected with clear errors.
7. No AF runtime import, duplicate hand-maintained registry, placeholder subsystem, mock production service, or unused abstraction remains.
8. A solution can resolve a capability to an immutable approved adapter release through the documented machine interface without executing adapter code or exposing a secret.
9. Every active adapter validates against the standard descriptor schema and exposes a clear value/use summary plus working links to its guide and knowledge base.
10. The catalogue/API distinguishes validated usage records from suggested use cases and returns both without overstating unproven claims.
11. Major prompts are versioned, schema-validated, and linked to privacy-aware execution records.
12. A fixture demonstrates detected drift, an evidence-backed evaluation record, and a versioned correction proposal visible without a dashboard.

## Required Design Review

Before finalising, conduct and document three independent review passes in `DESIGN_REVIEW.md`. Record every finding plus its resolution or an explicit, justified deferral; do not merely claim that review occurred.

1. **AI Engineer** — adapter contract completeness, provenance, SemVer, test isolation, schema/error semantics, secret handling, safety boundaries, and optional AF compatibility without coupling.
2. **Solution Architect** — ownership and dependency direction, solution adoption, promotion lifecycle, AF migration boundary, and avoidance of a central platform.
3. **Developer** — daily ergonomics, naming, simple commands, scaffold quality, CI, documentation, and maintainability.

## Handoff

Return:

1. the final file tree;
2. a short explanation of the contract and everyday workflows;
3. the AF migration inventory and the specific adapters migrated;
4. the milestone registry, completed milestone proofs, and commands run with their results;
5. `DESIGN_REVIEW.md` findings and resolutions;
6. an **Excluded by Design** list naming every tempting but intentionally omitted subsystem.
7. the mandatory **Review Triad** table from `docs/milestone_review_triad.md`. Show AI Engineer, Solution Architect, and Senior Developer on every material milestone or iteration hand-off, with truthful required/status, evidence, and next-action cells.

Do not pad the repository or the report. If something is not necessary for discovery, safe reuse, testing, versioning, or contribution, omit it.
