# Release and change policy

**Version:** 0.1.0  
**Owner:** Tool Repository maintainers  
**Review:** at every public release  
**Enforcement:** release/changelog validation delivered by `TR-M01`–`TR-M06`

Adapters, schemas, and reusable prompts use SemVer. Releases are immutable, and solution consumers resolve then pin exact versions.

Breaking contract, schema, or behavioural changes require a major version; compatible capabilities use a minor version; fixes and documentation-only corrections use a patch version. Every release has a concise changelog and identifies migration or replacement guidance when compatibility changes.

Changes must be proposed through a milestone, tested, and linked to a proof artifact. A policy or schema change also updates its version and adds a decision-log entry. Historical execution records remain immutable; corrections are new records that reference the original.
