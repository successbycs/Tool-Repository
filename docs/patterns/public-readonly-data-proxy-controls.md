# Public read-only data proxy controls

## Use when

A future adapter needs a bounded server-side read from an explicitly approved
public source. The adapter still executes in the consuming solution's own
environment; this document is not an approval to centralise execution.

## Required controls

1. Allow-list exact public source origins and paths; reject arbitrary URLs.
2. Define a minimal response contract and discard raw provider fields by
   default.
3. Permit reads only. No upstream writes, subscriptions, webhooks, or action
   endpoints are in scope.
4. Set explicit CORS origins appropriate to the consuming solution; do not use
   a wildcard as a convenience default.
5. Use a durable, deployment-appropriate cache and rate limiter. Process-local
   maps are not a reliable distributed control.
6. Return bounded errors without secrets, provider payloads, or internal
   topology.
7. Test denied origins, denied URLs, rate-limit behaviour, cache expiry, and
   minimal response filtering using non-sensitive fixtures.

## Do not use when

Provider terms are unknown, the source is private, any user data can enter the
request or response, or the solution needs a write path.

## Provenance and limitation

This control pattern was informed by the Pt Chev Water Times assessment. Its
source-specific proxy code, process-local caching, and rate-limit map are not
promoted because they are product-coupled and unsafe as reusable controls.
