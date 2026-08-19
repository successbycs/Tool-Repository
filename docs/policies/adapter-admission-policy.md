# Adapter admission policy

**Version:** 0.1.0  
**Owner:** Tool Repository maintainers  
**Review:** before each adapter release  
**Enforcement:** adapter manifest, schema, and conformance validators delivered by `TR-M01`–`TR-M03`

An adapter may be `active` only when it has a valid descriptor, owner, licence and provenance, documented security/side-effect classification, configuration schema, user guide, knowledge-base link, runnable example, and passing isolated conformance tests.

Default tests must not use credentials or a live network. Live checks are opt-in and must record their result without exposing secrets.

An adapter derived from a solution or AF must record origin, source revision, licence, and material changes. Duplicate or thin one-off wrappers are rejected. Unsafe or unmaintained adapters must be marked `deprecated` or `archived` with a replacement when one exists.
