# T480 MP4 transcription readiness

`mp4-transcription-t480` is a clean-room, read-only diagnostic adapter for a
fixed private transcription deployment. It exposes:

- `transcription_preflight` — inbox, output, and worker-image readiness.
- `transcription_runtime_status` — worker, local model-cache, and active-job
  count status.

The consumer supplies a `TranscriptionRuntimeProbe` over its reviewed fixed
transport. The adapter never uploads media, submits a transcription, starts a
worker, downloads a model, reads a private path, or accepts arbitrary commands.
It returns `transport_not_configured` until a probe is supplied.
