# Calendar event time-normalisation pattern

## Use when

A locally executed, read-only calendar adapter needs to present an approved
provider event to a user in an explicitly chosen IANA timezone.

## Rules

1. Preserve the provider event instant as received; conversion is presentation,
   not a rewrite of the provider record.
2. Convert that instant using the consumer-selected IANA timezone, including DST
   and date-boundary handling.
3. Treat a time embedded in an event title as editorial metadata. It may be
   displayed only when an approved consumer contract explicitly selects
   `title_metadata`; it must never silently replace the provider instant.
4. If title metadata is missing or malformed, fall back to the converted event
   instant and record that source choice in the normalised output.
5. Keep recurrence expansion, provider timezone assumptions, and source data
   corrections outside this asset until a specific adapter contract approves them.

## Fixture boundary

`fixtures/calendar-event-time-normalisation/expected.json` is synthetic,
non-sensitive evidence for summer time, winter time, midnight rollover, and
malformed title metadata. It is not raw provider calendar data.

## Do not use when

The source timezone is unknown, a user expects scheduling or calendar writes,
or an application needs to infer an editorial time automatically.

## Provenance and limitation

This is a clean-room pattern informed by the MIT-licensed Pt Chev Water Times
assessment. It does not extract source code or approve an executable adapter.
