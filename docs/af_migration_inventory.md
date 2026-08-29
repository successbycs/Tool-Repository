# TR-M05 clean-room migration inventory

## Decision boundary

The repository owner authorised internal/proprietary reuse on 2026-08-29 for
the two local source repositories below. This milestone is a clean-room
implementation: it records behaviour and safety boundaries but does not copy
source code, local configuration, credentials, media, or historical runtime
proof.

| Source | Revision inspected | Candidate | Decision | Destination |
| --- | --- | --- | --- | --- |
| `/home/chris/projects/cs-ai-lab-infra` | `551f1afe972172ba9eee707a81a12072c8473ee0` | Strict T480 target validation and fixed lab health concepts | Extract as clean-room, read-only components | `adapters/t480-transport`, `adapters/t480-lab` |
| `/home/chris/projects/mp4-to-transcript` | `85af3a676f689cf67cfc8e63913b133e0bd5c704` | Fixed transcription preflight and runtime-status concepts | Extract as a clean-room, read-only component | `adapters/mp4-transcription-t480` |
| `/home/chris/SuccessByCS-Builder/Autonomous-Framework` | `d4ac29c34493659b9d46c42725f1673c1e7abc0e` | Broad adapter and CLI patterns | Reference only for this milestone | None |

## Deliberate reductions

- Transport validates a bounded target only; it does not establish a connection.
- Lab readiness uses a consumer-injected fixed probe and reports six booleans.
- Transcription reports readiness only; it cannot transfer media, start jobs,
  obtain models, or modify the T480.
- Tests use fake probes. Live access is out of scope for TR-M05.

## Admission evidence

Each destination has a static descriptor, a knowledge record, a short guide,
and conformance coverage in `tests/test_conformance.py`. Descriptors remain
`draft` until the release and catalogue milestones make an immutable consumption
path available.
