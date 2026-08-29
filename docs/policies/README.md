# Policies

Policies turn the delivery plan into enforceable operating rules. They are versioned repository documents, not a separate framework.

| Policy | Governs | Enforcement target |
| --- | --- | --- |
| [Milestone policy](milestone-policy.md) | status transitions, closure, and ingestion declarations | milestone schema and validator |
| [Adapter admission policy](adapter-admission-policy.md) | active/deprecated adapters | manifest and conformance validation |
| [Knowledge policy](knowledge-policy.md) | tool guides and usage learning | knowledge/manifest validation |
| [Prompt data policy](prompt-data-policy.md) | prompt capture and privacy | prompt-record validation |
| [Release and change policy](release-and-change-policy.md) | versions and compatibility | release checks and changelog validation |

Any policy change must identify its enforcement change, increment the policy version, and be recorded in the decision log. If it cannot be enforced now, the policy must say so explicitly and name the milestone that will add enforcement.

The mandatory delivery-chat review table is documented in [Milestone review triad](../milestone_review_triad.md) and instructed through the repository-root `AGENTS.md`.
