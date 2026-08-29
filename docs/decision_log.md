# Decision log

## 2026-08-17 — Tool Repository is the shared adapter library

The Tool Repository owns reusable adapter code, descriptors, knowledge, tests, and release metadata. Autonomous Framework is a candidate source of patterns and adapters, not a runtime dependency or control plane.

## 2026-08-17 — Milestone policy precedes adapter implementation

The repository will not treat a milestone registry as sufficient governance. `TR-M00` establishes the minimal policy and validation baseline before implementation milestones may close.

## 2026-08-17 — Evidence outranks claims

Milestone closure requires reproducible verification and an inspectable proof artifact. Prompt logs, plans, and JSON summaries alone do not prove a tool or external-system outcome.

## 2026-08-17 — CS AI Lab deployment is a release gate, not an early API deployment

The Tool Repository will first deploy immutable library releases to the CS AI Lab laptop through a non-root, versioned installation with verification and rollback. A read-only catalogue API may be deployed only after it exists as a generated and tested `TR-M04` capability.

## 2026-08-17 — Repository reuse requires one-at-a-time evidence-based intake

Source repositories are assessed read-only and one at a time before any asset is promoted. Adapters, workflows, RAG templates, Apify crawlers, prompts, and evaluation assets are candidates only when provenance, licence, security, configuration boundaries, and repeatable value are documented.

## 2026-08-17 — The repository goal is measured by safe reuse, not asset count

The Tool Repository exists to make trusted assets discoverable, understandable, testable, and reusable in a new solution within minutes. It will prioritise isolated quality, clear guides, immutable versions, and successful reuse over collecting a large catalogue.

## 2026-08-17 — Every material hand-off shows the review triad

Codex must show AI Engineer, Solution Architect, and Senior Developer review state after every material milestone or iteration hand-off. `AGENTS.md` carries the executor instruction, the milestone policy defines truthful statuses, and the stored review/proof records remain the durable evidence.

## 2026-08-29 — New closure evidence is commit-bound

New high-risk corrective milestones require a full inspectable commit SHA, matching verification-output hashes, and hashed saved review records. Historical proofs are preserved as records rather than rewritten.

## 2026-08-29 — T480 migration uses clean-room components

The repository owner authorised internal/proprietary reuse of the local CS AI Lab and MP4 transcription repositories. TR-M05 will create separately versioned clean-room transport, lab, and MP4 components without copying source code or machine-local configuration.

## 2026-08-29 — Catalogue publication uses Cloudflare R2

After TR-M04 generates and validates immutable catalogue JSON, GitHub CI will
publish it to a private Cloudflare R2 bucket. The subscribed Cloudflare Worker
will be the stateless HTTPS catalogue endpoint; neither R2 nor the Worker may
execute adapters or hold solution secrets.

## 2026-08-29 — First local release is v0.1.0

TR-M01A promotes the library package from `0.0.0` to `0.1.0` and binds the
first CS AI Lab installation to the exact local Git tag `v0.1.0`. The install
uses a non-root, versioned release directory and records the resolved commit;
the tag is not a mutable runtime dependency.

The existing `v0.0.0` package commit is retained locally as the rollback
baseline. It is installed only to exercise rollback and then `v0.1.0` is
restored as the selected release.
