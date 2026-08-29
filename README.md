# Tool Repository

## Goal

Make trusted integration assets easy to discover, understand, test, consume, improve, and safely reuse across solutions.

The practical test is simple: a developer starting a new solution can find a suitable asset, understand its value and limits, configure it safely, run its default tests, and use a pinned version in under ten minutes.

## What it can do now

- validate reusable adapter contracts, descriptors, guides, knowledge records,
  provenance, safety boundaries, and isolated conformance tests;
- provide three draft, read-only reference adapters for T480 target validation,
  CS AI Lab readiness, and MP4-transcription environment readiness;
- generate a static, read-only [adapter catalogue](catalogue/adapters.json)
  that binds every listed adapter to a trusted publisher, immutable Git tag and
  commit, release URI, and descriptor SHA-256;
- let another solution resolve a catalogue entry, pin and verify the exact
  release locally, then invoke the adapter within its own process. See the
  [minimal consumption example](examples/minimal-solution/README.md);
- retain provenance for solution-owned forks and provide a documented route to
  promote genuinely reusable improvements back into this repository; and
- install, verify, update, and roll back the versioned library release on the
  local CS AI Lab machine without privileged runtime access; and
- validate versioned reusable prompts and privacy-safe, hash-bound execution
  provenance without retaining raw prompts, private content, credentials, or
  hidden reasoning.

The catalogue is a discovery and release-verification document only. It never
executes adapters, receives solution secrets, or becomes a central control
plane.

## Still to come

- publish the generated catalogue through Cloudflare R2 and a stateless Worker
  HTTPS endpoint; and
- complete prompt evaluation and drift-correction capabilities.

## What this repository owns

- reusable adapters, workflow recipes, solution templates, prompts, schemas, evaluation assets, and operational knowledge;
- one standard descriptor and contract for active assets;
- provenance, licence, lifecycle, tests, guides, and release metadata;
- a read-only catalogue/release-resolution interface when that capability is implemented;
- one-repository-at-a-time intake and evidence-backed promotion of external assets.

## What it does not own

- product/domain logic, customer data models, user interfaces, or solution-specific deployment configuration;
- solution secrets and credentials;
- an agent framework, workflow runtime, marketplace, central adapter-execution proxy, or general-purpose control plane.

Autonomous Framework is a candidate source of useful patterns and assets. It is not a runtime dependency.

## Operating principles

1. **Evidence before inclusion.** An asset is not active because it looks useful; it needs provenance, a clear reusable boundary, tests, documentation, and an acceptance path.
2. **Smallest portable unit.** Reuse the smallest independently buildable and testable asset, not an entire source repository by default.
3. **Safe by default.** Default tests use fakes and no credentials or network; destructive actions are explicit and opt-in; secrets never enter manifests, guides, or logs.
4. **Humans and automation can both understand it.** Manifests, JSON Schemas, guides, and the catalogue explain purpose, inputs, outputs, limitations, and safe use.
5. **Solutions consume immutable releases.** A solution pins a version. Forks retain source provenance; reusable improvements return through a reviewed promotion path.
6. **Learning is part of the asset.** Every active asset has a user guide, validated usage records, clearly labelled suggested uses, limitations, and an owner.
7. **No false completion.** Milestones close only with reproducible verification and inspectable proof; prompts and plans are audit evidence, not proof of an outcome.

## How success is measured

- time for a new solution to discover, configure, test, and consume an asset;
- active assets with valid schema, provenance/licence, guide, owner, and isolated test path;
- default-test pass rate and regression-free upgrades;
- rate of successful reuse versus one-off copying;
- stale assets visibly deprecated or archived;
- adoption and correction evidence for reusable prompts and AI assets.

## Delivery

The repository is built through governed milestones in [milestone_registry.json](milestone_registry.json). The completed governance baseline and operating documents are indexed in [docs](docs/README.md). The build brief is [PROMPT.md](PROMPT.md).
