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
- [CS AI Lab deployment](cs_ai_lab_deployment.md) describes the non-root,
  versioned local release path and rollback contract.

`milestone_registry.json` is the delivery plan. A proof artifact records what actually happened. Neither may be edited to make an unverified result appear complete.
