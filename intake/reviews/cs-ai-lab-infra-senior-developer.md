# CS AI Lab infrastructure — Senior Developer review

## Blocking

- The target bridge and deployment details are coupled to private infrastructure and are not independently testable here.

## Required before active

- Separate a fixed-operation transport seam, use fakes by default, and document non-root deployment and rollback.

## Recommended

- Do not migrate Docker or Compose configuration as adapter source.
