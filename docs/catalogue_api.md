# Read-only catalogue API

TR-M04 generates `catalogue/adapters.json` from static `adapter.json` files
and `catalogue/release-index.json`. It never imports adapter modules, opens a
transport, or reads solution configuration.

Build and validate it locally:

```bash
PYTHONPATH=src python3 -m tool_repository catalogue build
PYTHONPATH=src python3 -m tool_repository catalogue validate
```

## Consumer contract

The future Cloudflare Worker serves this exact immutable document at
`GET /catalogue/v1/adapters.json`. Consumers select an entry by
`adapter.id` and `adapter.version`, then pin the `release.release_tag` and
`release.release_commit`. They verify the descriptor byte hash against
`manifest_sha256` before using the release.

Every entry contains the static value/fit/limitations, capabilities and
operations, guide and knowledge paths, descriptor hash, and immutable Git
release reference. It contains no adapter result, secret, host configuration,
customer data, or execution endpoint.

## Trust and publication

The release index declares trusted publishers and binds every current
descriptor version to a tag, full commit, artifact URI, and descriptor SHA-256.
The build rejects an untrusted publisher, malformed release reference, missing
entry, stale entry, duplicate entry, or a descriptor checksum mismatch.

GitHub CI will publish the generated file plus its checksum to private R2 only
after this local contract passes. The Worker is a stateless reader; its R2
binding and deployment credentials are intentionally deferred to the Cloudflare
publication implementation.
