# Tool Repository operating documents

These documents govern delivery of this repository. They are intentionally small:

- [Repository goal](../README.md) defines the reusable value this repository must create.
- [Milestone execution](milestone_execution.md) tells an executor how to take a milestone from `not_started` to a truthful result.
- [Policies](policies/README.md) define the rules that the milestone registry alone cannot express.
- [Decision log](decision_log.md) records durable choices and their rationale.
- [Completed-state architecture](architecture.md) shows the repository's
  intended library, intake, release, knowledge, and solution-consumption boundaries.
- [Catalogue deployment architecture](catalogue_deployment_architecture.md)
  defines GitHub-to-Cloudflare R2 publication for the future read-only catalogue.
- [Target operating model](target_operating_model.md) maps what users can do
  today and the staged path to hosted catalogue discovery.
- [Public read-only calendar reader pattern](patterns/public-readonly-calendar-reader.md)
  defines the safe boundary for a future clean-room calendar adapter.
- [Catalogue API](catalogue_api.md) defines the generated read-only discovery
  document and consumer pinning contract.
- [Catalogue ingestion standard](catalogue_ingestion.md) defines the required
  promotion flow for adapters, local models, prompts, and harvested assets.
- [Adapter lifecycle](adapter_lifecycle.md) defines how solutions consume,
  upgrade, fork, and retire immutable adapter releases.
- [Contributing adapters](contributing_adapters.md) defines the provenance and
  promotion path for reusable solution improvements.
- [Prompt library standard](prompt_library_standard.md) defines versioned,
  privacy-safe reusable prompts and execution provenance.
- [Goal prompt and approval flow](goal_prompt.md) defines how a prompt-assisted
  goal becomes an explicitly human-approved milestone seed and catalogue entry.
- [Prompt drift model](prompt_drift_model.md) and
  [evaluation policy](prompt_evaluation_policy.md) define reproducible
  regression detection and human-controlled correction proposals.
- [CS AI Lab deployment](cs_ai_lab_deployment.md) describes the non-root,
  versioned local release path and rollback contract.

`milestone_registry.json` is the delivery plan. A proof artifact records what actually happened. Neither may be edited to make an unverified result appear complete.
