# CS AI Lab deployment

TR-M01A installs an exact Git tag as a non-root, versioned local release. It
does not run an adapter service, open ingress, create a database, or require
Docker.

On host `Piwakawaka`, account `chris`, the first release is `v0.1.0`:

```bash
deploy/cs-ai-lab/install.sh \
  --source /home/chris/Tool-Repository \
  --release v0.1.0 \
  --install-root /home/chris/.local/share/tool-repository \
  --account chris
```

The installer resolves the tag to a commit, archives that commit into
`releases/vX.Y.Z-COMMIT12`, writes `release.json`, and atomically points
`current` at that release. It refuses root, a mutable directory in place of the
`current` symlink, a missing tag, or unsafe paths.

Verify the selected release without exposing secrets:

```bash
python3 scripts/verify_cs_ai_lab_deploy.py \
  --host Piwakawaka --account chris --release v0.1.0 \
  --source /home/chris/Tool-Repository \
  --install-root /home/chris/.local/share/tool-repository
```
