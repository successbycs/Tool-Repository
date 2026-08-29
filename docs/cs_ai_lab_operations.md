# CS AI Lab release operations

List the versioned local releases under
`/home/chris/.local/share/tool-repository/releases`. `current/release.json`
records the selected tag and exact commit.

To roll back, select an existing release identifier printed by the installer:

```bash
deploy/cs-ai-lab/rollback.sh \
  --install-root /home/chris/.local/share/tool-repository \
  --release-id v0.1.0-COMMIT12 \
  --account chris
```

Rollback only switches the `current` symlink. It does not delete a release,
change remote Git state, deploy a Worker, execute an adapter, or alter a T480
service. After every install or rollback, run the deployment verification
command in [CS AI Lab deployment](cs_ai_lab_deployment.md).
