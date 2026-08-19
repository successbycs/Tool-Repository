# Knowledge-base contract fixture

This is a deliberately safe fixture, not an active adapter and not evidence of
production use. It demonstrates the two record types required for each tool:

- `validated_usage` records a dated, bounded observed outcome and a safe
  evidence reference.
- `suggested_use` records a possible use with its assumptions and the
  validation still required. It is never presented as proven.

The fixture uses fake transport only, contains no credentials or customer data,
and exists so the default validation command has non-vacuous contract evidence
before a real adapter is migrated.
