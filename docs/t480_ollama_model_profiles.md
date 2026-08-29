# T480 local Ollama model profiles

`catalogue/t480-ollama-model-profiles.json` is the approved, static model
profile set observed on **Piwakawaka** (the T480 / CS AI Lab host). Its digest,
size, parameter count, and quantization describe one observed local install;
a model tag alone is never its identity.

The generated read-only catalogue exposes these profiles in
`model_profiles`. This is metadata for selection and verification, not a
model-serving API or an adapter that can run prompts.

## Available roles

| Profile | Intended use | Input |
| --- | --- | --- |
| `qwen3-4b-q4` | Small local reasoning, routing, structured extraction | Text |
| `qwen2.5-coder-7b-q4` | Local code assistance and structured tool use | Text |

All profiles are `active` and `local_only: true`. A local application on the
T480 may call Ollama at `http://127.0.0.1:11434`; no other repository should
call that port directly. It is intentionally loopback-only and no public or
Cloudflare endpoint is created by this milestone.

## Safe consumer flow

1. Select a profile by its stable profile ID and intended role.
2. Require `local_only: true`; never convert this metadata into a public URL.
3. On the T480, compare `GET /api/tags` with the profile's full digest before
   submitting any work.
4. Use the model only for the role and limitations recorded in the profile.

Run the read-only verification check from the T480:

```bash
python3 scripts/verify_t480_ollama_profiles.py
```

The check refuses non-loopback URLs and compares every recorded model's exact
digest, byte size, parameter count, and quantization with Ollama's local
`/api/tags` response. It does not send prompts or expose a network service.

## Refreshing a profile

After an authorised `ollama pull`, first record the new `/api/tags` result.
Update the static profile's tag, full digest, size, model details, intended
roles, and limitations together. Then run the profile verifier, catalogue
build, and tests before publishing a new immutable catalogue release.

Remote projects that need inference must use a future separate authenticated
job/gateway adapter. That design must enforce authentication, request limits,
and data handling; the catalogue remains read-only discovery metadata.
