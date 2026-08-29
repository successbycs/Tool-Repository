# Adapter lifecycle

An adapter has two independent stories: its repository lifecycle and each
solution's consumption decision. A solution may pin an existing release, keep
using it, upgrade, or retire it; it does not change the adapter's repository
state by doing so.

| Repository state | Meaning | Required evidence / action |
| --- | --- | --- |
| candidate | Found through intake; not reusable yet. | Provenance, licence, safety assessment. |
| draft | Descriptor and boundaries exist but the adapter is not approved for general use. | Isolated tests and an owner before activation. |
| active | Approved reusable release. | Immutable tag/commit, descriptor hash, guide, knowledge, and conformance proof. |
| deprecated | Existing consumers may migrate; no new use is recommended. | Replacement or migration guidance and a visible reason. |
| archived | No longer supported. | Retain provenance and historical release evidence. |

## Solution consumption loop

1. Discover an adapter in the read-only catalogue and assess its static fit,
   limits, data classification, and side effects.
2. Resolve and record the adapter ID, version, publisher, tag, full commit,
   artifact URI, descriptor hash, and catalogue release-index hash in the
   solution lock file.
3. Check out the exact commit locally, verify the descriptor hash, run the
   safe default test or health path, then call the adapter inside the solution.
4. Keep solution configuration and secrets inside the solution. A catalogue
   request never becomes an adapter-execution request.
5. If the solution needs a change, choose between a solution-owned wrapper and
   a separately owned fork. Record the originating immutable release either
   way.
6. Propose a generalisable improvement back only through the contribution
   process. The Tool Repository releases the accepted change as a new,
   immutable version; consumers opt in by updating their lock.

This avoids both mutable shared dependencies and duplicated solution-local
catalogues. The minimal executable example is
[`examples/minimal-solution`](../examples/minimal-solution/README.md).
