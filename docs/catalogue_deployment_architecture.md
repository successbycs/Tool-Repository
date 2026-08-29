# Catalogue deployment architecture

## Purpose

The Tool Repository catalogue is a generated, immutable JSON document. It is a
discovery and release-resolution surface only; it never executes an adapter,
stores solution configuration or secrets, or requires a database.

## Hosting model

GitHub remains the source of truth for code, CI, tagged releases, and release
assets. The TR-M04 release workflow generates `catalogue/adapters.json`,
validates it, calculates its checksum, and publishes that exact versioned file
to a private Cloudflare R2 bucket. A Cloudflare Worker is the planned HTTPS
catalogue endpoint and reads only the published JSON object.

```text
GitHub tag and CI
  -> generate and validate catalogue/adapters.json
  -> upload versioned JSON plus checksum to private Cloudflare R2
  -> Cloudflare Worker serves the immutable catalogue over HTTPS
  -> solution resolves and installs its adapter locally
```

The Worker exposes static paths such as `/catalogue/v1/adapters.json` and may
offer a stable `/catalogue/latest` alias. It must remain stateless, serve only
catalogue data, and perform no adapter execution.

## Boundaries

- The CS AI Lab installation validates and builds releases; it is not the
  required always-on catalogue host.
- Cloudflare R2 hosts generated metadata privately. The Worker returns only
  approved catalogue content; no adapter code executes there and no solution
  secret is uploaded there.
- Consumers validate the declared checksum and pin an exact adapter release.
- Publication credentials live only in CI secrets; they are never included in
  descriptors, proofs, or the catalogue.
