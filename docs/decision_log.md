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
