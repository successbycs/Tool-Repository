# Contributing adapter improvements

## First decide where the change belongs

Keep a change in the solution when it contains product/domain behaviour,
customer data models, solution secrets, deployment configuration, or a
one-off workflow. Propose it here when its boundary, value, safety controls,
and tests are useful across solutions.

Never edit a pinned vendor checkout and represent it as an upstream release.
Create an explicitly owned wrapper or fork instead, then preserve the source
release provenance.

## Required fork provenance

Before proposing a reusable fork, record:

- original adapter ID and version;
- original tag, full commit, artifact URI, and descriptor SHA-256;
- local owner and asset ID;
- material changes and the reason they are generalisable; and
- whether the change is merely a wrapper, a compatible extension, or a
  breaking replacement.

[`examples/minimal-solution/local-fork-provenance.json`](../examples/minimal-solution/local-fork-provenance.json)
is a complete safe example. Do not include secrets, target hostnames, customer
data, or operation results in provenance.

## Promotion path

1. Submit the provenance record and a concise reusable problem statement.
2. Perform or update read-only intake; confirm source, licence, security
   posture, ownership, and destination.
3. Add or amend the adapter descriptor, guide, knowledge records, and isolated
   fake-backed tests. Preserve the original source reference in the descriptor.
4. Run contract and manifest conformance validation. Review safety, lifecycle,
   SemVer impact, migration guidance, and all evidence.
5. After acceptance, publish a new immutable tag and release-index entry. The
   contributing solution remains on its old lock until it deliberately resolves
   and validates the new release.

The repository will reject thin duplicates, undisclosed source changes,
unverified live-network behaviour, and changes that make it a central adapter
execution service.
