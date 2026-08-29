# Completed-state architecture

![Completed Tool Repository architecture](assets/tool-repository-completed-architecture.png)

The Tool Repository is a source-first, governed library of reusable adapters.
It accepts candidate assets only through read-only intake, retains their
descriptor, schema, knowledge, tests, conformance evidence, and reviews, then
publishes immutable releases for solution repositories to consume locally.

It does not execute adapters centrally, store solution secrets, or require a
database. The CS AI Lab installs versioned repository releases under a non-root
account and can roll back locally. A future catalogue is read-only discovery and
release resolution, published as immutable JSON to Cloudflare R2; adapter
execution remains inside each consuming solution. See the
[catalogue deployment architecture](catalogue_deployment_architecture.md).

## Solution consumption and contribution

A solution selects a catalogue entry, records the adapter version, tag, full
commit, artefact URI, descriptor hash, and release-index hash in its own lock
file, then checks out and invokes that release locally. It does not get an
execution endpoint from the catalogue.

When a solution needs a reusable improvement, it keeps a provenance record for
its exact source release and proposes the change through intake, isolated
tests, review, and a new immutable release. The executable reference is the
[minimal solution example](../examples/minimal-solution/README.md).

## Prompt assets and provenance

Reusable prompts are static, versioned definitions. A solution may retain an
execution provenance record that binds a definition hash, context, runtime,
redacted/protected fingerprints, and outcome evidence. Raw prompts, private
content, credentials, and hidden reasoning stay outside this repository and
outside any central execution service.

Prompt evaluation runs against versioned, non-sensitive fixtures with a
calibrated evaluator profile and explicit rubric thresholds. Reports surface
per-dimension and overall drift, a correction proposal, and a non-regression
comparison. They never auto-promote a prompt version.

## Knowledge relationship

Each active adapter links its user guide and JSON knowledge records from its
`adapter.json` descriptor. Knowledge distinguishes validated, evidenced use from
suggested use. It is part of the adapter release, not a separate runtime or
central service.
