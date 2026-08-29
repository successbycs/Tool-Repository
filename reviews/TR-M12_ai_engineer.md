# TR-M12 AI Engineer review

Passed: the profile set makes local-model selection explicit by recording each
model's intended role, modalities, limitations, exact installed digest, size,
parameter count, and quantisation. The local verifier compares all of those
runtime-visible fields against Ollama rather than trusting a mutable tag.

Advice: retain the digest check whenever a model is refreshed and add measured
latency/quality evaluations before presenting any profile as suitable for
high-stakes reasoning or autonomous action.
