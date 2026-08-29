#!/usr/bin/env bash
# Switch the current non-root install to a previous immutable release directory.
set -euo pipefail

usage() {
  echo "Usage: rollback.sh --install-root PATH --release-id vX.Y.Z-COMMIT12 --account USER" >&2
}

install_root=""
release_id=""
account=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-root|--release-id|--account)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      case "$1" in
        --install-root) install_root="$2" ;;
        --release-id) release_id="$2" ;;
        --account) account="$2" ;;
      esac
      shift 2 ;;
    *) usage; exit 2 ;;
  esac
done

[[ "$install_root" == /* && "$install_root" != / ]] || { echo "install root must be a safe absolute path" >&2; exit 2; }
[[ "$release_id" =~ ^v[0-9]+\.[0-9]+\.[0-9]+-[0-9a-f]{12}$ ]] || { echo "release id is invalid" >&2; exit 2; }
[[ "$account" =~ ^[a-z_][a-z0-9_-]*$ && "$(id -un)" == "$account" ]] || { echo "rollback must run as the declared non-root account" >&2; exit 2; }
target="$install_root/releases/$release_id"
[[ -d "$target" && -f "$target/release.json" ]] || { echo "requested immutable release does not exist" >&2; exit 2; }
if [[ -e "$install_root/current" && ! -L "$install_root/current" ]]; then
  echo "current must be absent or a symlink" >&2
  exit 2
fi
pending_link="$install_root/.current-${release_id}.tmp"
ln -s "$target" "$pending_link"
mv -Tf "$pending_link" "$install_root/current"
printf '%s\n' "$target/release.json"
