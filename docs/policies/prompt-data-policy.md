# Prompt data policy

**Version:** 0.1.0  
**Owner:** Solution owner for execution records; Tool Repository maintainers for reusable prompt definitions  
**Review:** before prompt-library release and after any data-classification change  
**Enforcement:** prompt schemas and record validation to be delivered as a dedicated milestone

Major prompts for intake, assessment, planning, implementation, review, QA, and remediation must have a stable ID, version, purpose, input/output contract, constraints, and owner.

Each execution records the prompt version/hash, milestone/solution context, runtime/model, redacted input fingerprint, output reference/hash, timestamp, and outcome. Store the exact rendered prompt only when permitted by its data classification.

Never store credentials, tokens, private customer content, or hidden reasoning. When full capture is not permitted, store a redacted canonical representation plus hash and protected reference. Prompt records are audit evidence only: acceptance still requires the milestone's declared verification and proof.
