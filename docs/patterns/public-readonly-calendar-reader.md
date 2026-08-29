# Public read-only calendar reader pattern

## Use when

A solution needs bounded discovery from an explicitly approved public calendar
feed and can execute its selected adapter locally.

## Pattern

1. A human approves an exact provider/feed reference and the fields permitted
   to leave that provider.
2. The adapter accepts no arbitrary URL; it reads only the approved source and
   a bounded date range.
3. It normalises a minimal event contract and records source/freshness metadata.
4. The consumer chooses its own display timezone. Provider timestamps remain
   distinct from editorial title text or local display conventions.
5. All default tests use static, non-sensitive iCalendar fixtures and fake
   provider responses.

## Do not use when

The source is private, its terms are unknown, events can expose personal data,
or the solution needs calendar writes, subscriptions, webhooks, or arbitrary
outbound fetching.

## Evidence and limitations

This pattern was staged from the MIT-licensed Pt Chev Water Times source
assessment. It is not a code extraction. Its source parser, process-local
cache, and rate-limiting map are reference-only and not an approved adapter
implementation.
