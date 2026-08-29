# Minimal solution: consume a pinned adapter

This example models a separate solution repository. It consumes the
read-only `t480-transport` adapter at one immutable release, rather than
calling a central Tool Repository service or copying a mutable adapter.

## What is pinned

`tool-repository.lock.json` binds the solution to:

- `t480-transport@0.1.0`;
- the Git tag **and** full commit `ee92b26d407a49422560d0a3e98b0fb9764ee6a2`;
- the descriptor SHA-256; and
- the release-index hash used to resolve it.

The exact commit is the authority. A tag makes the release understandable, but
the consumer verifies both the checked-out commit and the descriptor bytes.

## Consume it

Copy this directory into the solution repository, download the published
read-only catalogue, then make a clean checkout of the pinned source release:

```bash
git clone https://github.com/successbycs/Tool-Repository.git vendor/tool-repository
git -C vendor/tool-repository checkout --detach ee92b26d407a49422560d0a3e98b0fb9764ee6a2
curl --fail --silent --show-error \
  https://<catalogue-host>/catalogue/v1/adapters.json \
  --output vendor/tool-repository-catalogue.json
PYTHONPATH=vendor/tool-repository/src python consume_locked_adapter.py \
  --tool-repository vendor/tool-repository \
  --catalogue vendor/tool-repository-catalogue.json \
  --target operator@t480
```

The sample performs one read-only operation, `validate_target`. Its result is
local to the solution. The catalogue only helps discovery and verification; it
does not receive target configuration, secrets, logs, or operation calls.

For the local repository demonstration, replace the downloaded catalogue path
with `../../catalogue/adapters.json` and use a detached worktree at the locked
commit. The test suite performs exactly that check without a network call.

## Fork only when needed

The solution uses the adapter unchanged by default. If it needs a reusable
change, create a separately owned local adapter or wrapper and retain
`local-fork-provenance.json` with the original ID, exact release, commit,
artifact URI, descriptor hash, owner, and material changes. Do not edit the
vendored checkout and call it an upstream release.

When the change may benefit more than this solution, follow
[the contribution guide](../../docs/contributing_adapters.md). It is promoted
only after repository intake, descriptor/knowledge updates, isolated tests,
review, and a new immutable release.
