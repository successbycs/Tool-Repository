# Target operating model

## Purpose

The Tool Repository is a governed, read-only discovery and release-resolution
service. It helps a solution find a suitable reusable asset, verify its exact
release, acquire it deliberately, and run it in the solution's own environment.
It is never a central adapter-execution service, model proxy, customer-data
store, or secret store.

## User workflow

```text
solution need
  -> fetch approved catalogue
  -> select a suitable capability and inspect limits
  -> pin the release tag, commit, and descriptor hash
  -> deliberately acquire the pinned adapter release
  -> configure and execute locally in the solution environment
  -> propose reusable improvements through governed intake
```

When no approved asset fits, a user creates a goal candidate. A repository
owner approves the goal before it becomes milestone work. Ingestion, tests,
proof, and the Review Triad are then required before the new metadata enters
the catalogue.

## Capability map

Status is intentionally narrow: **completed** means a checked-in, validated
capability exists; **in progress** means active bounded delivery work exists;
and **not started** means only the design or roadmap exists. A capability may
have a completed local form while its hosted form is not started.

| Capability | User-visible result | Status | Milestone mapping |
| --- | --- | --- | --- |
| Governance, intake, proof, and review | New reusable assets follow an evidence-backed admission path. | completed | TR-M00, TR-M09, TR-M10, TR-M14, TR-M16 |
| Static catalogue generation | A validated JSON catalogue lists approved adapters, local model profiles, prompts, templates, and goals. | completed | TR-M04, TR-M12, TR-M16 |
| Immutable release resolution | A catalogue entry binds an adapter to a Git tag, full commit, descriptor hash, and release URI. | completed | TR-M01A, TR-M04, TR-M15 |
| Local consumer workflow | A solution can read a downloaded catalogue, verify a lock file, check out a pinned release, and invoke it locally. | completed | TR-M01A, TR-M06 |
| CI validation | GitHub validates repository contracts and tests on pushes and pull requests. | completed | TR-M10, TR-M11 |
| Target operating model and delivery roadmap | Maintainers and users can distinguish available local capability from future hosted capability. | completed | TR-M17 |
| Immutable hosted catalogue objects | A validated catalogue and checksum are published to private Cloudflare R2 from GitHub CI. | not started | TR-M18 |
| Protected HTTPS catalogue API | A stateless Cloudflare Worker serves immutable catalogue JSON and no adapter execution endpoint. | not started | TR-M19 |
| HTTP catalogue consumer | A consuming repository fetches, caches, validates, and pins the hosted catalogue. | not started | TR-M20 |
| Guided adapter acquisition | A consumer deliberately acquires a pinned adapter release and installs it non-root locally. | not started | TR-M21 |
| Hosted service assurance | Access control, deployment rollback, logs, health checks, and operational runbooks protect the hosted catalogue. | not started | TR-M22 |

## Target deployment flow

```text
GitHub source + tagged release
  -> CI validates and generates catalogue JSON + checksum
  -> TR-M18 publishes immutable objects to private Cloudflare R2
  -> TR-M19 Worker verifies access and serves read-only HTTPS responses
  -> TR-M20 consumer validates checksum and pins selected release
  -> TR-M21 consumer checks out or installs the exact release locally
  -> adapter executes only in the consumer-approved environment
```

## Delivery order

1. TR-M17 is complete; the model and roadmap are the current source of truth.
2. Build TR-M18 next, before exposing any hosted data: R2 publication must be
   deterministic, least-privilege, and rollback-capable.
3. Build TR-M19 only on the R2 artifact contract. The first API is one
   read-only document path, not search, execution, or mutation endpoints.
4. Build TR-M20 and TR-M21 for consumer convenience after the provider surface
   is stable.
5. Build TR-M22 before treating the endpoint as a dependable shared service.

The earlier local/Git workflow remains valid throughout. Hosted access extends
discovery; it does not change the immutable release or local-execution boundary.
