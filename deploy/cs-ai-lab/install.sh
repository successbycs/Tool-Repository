#!/usr/bin/env bash
# Install one immutable Tool Repository Git release without root privileges.
set -euo pipefail

usage() {
  echo "Usage: install.sh --source PATH --release vX.Y.Z --install-root PATH --account USER" >&2
}

source_path=""
release_tag=""
install_root=""
account=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source|--release|--install-root|--account)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      case "$1" in
        --source) source_path="$2" ;;
        --release) release_tag="$2" ;;
        --install-root) install_root="$2" ;;
        --account) account="$2" ;;
      esac
      shift 2 ;;
    *) usage; exit 2 ;;
  esac
done

[[ "$source_path" == /* && "$install_root" == /* && "$install_root" != / ]] || { echo "source and install root must be safe absolute paths" >&2; exit 2; }
[[ "$release_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "release must be an exact vX.Y.Z tag" >&2; exit 2; }
[[ "$account" =~ ^[a-z_][a-z0-9_-]*$ && "$(id -un)" == "$account" ]] || { echo "installer must run as the declared non-root account" >&2; exit 2; }
[[ "$source_path" != *'"'* && "$install_root" != *'"'* ]] || { echo "paths containing quotes are not supported" >&2; exit 2; }
[[ -d "$source_path/.git" ]] || { echo "source must be a Git working tree" >&2; exit 2; }

commit="$(git -C "$source_path" rev-parse --verify "${release_tag}^{commit}")"
release_id="${release_tag}-${commit:0:12}"
releases_dir="$install_root/releases"
destination="$releases_dir/$release_id"
mkdir -p "$releases_dir"
[[ -d "$releases_dir" && -w "$releases_dir" ]] || { echo "release directory is not writable" >&2; exit 2; }
if [[ -e "$install_root/current" && ! -L "$install_root/current" ]]; then
  echo "current must be absent or a symlink" >&2
  exit 2
fi

if [[ -e "$destination" ]]; then
  [[ -f "$destination/release.json" ]] || { echo "existing release directory has no metadata" >&2; exit 2; }
  grep -Fq "\"commit\": \"$commit\"" "$destination/release.json" || { echo "existing release does not match resolved commit" >&2; exit 2; }
else
  staging="$(mktemp -d "$releases_dir/.install.XXXXXX")"
  trap 'rm -rf "$staging"' EXIT
  git -C "$source_path" archive "$commit" | tar -x -C "$staging"
  printf '{\n  "release_tag": "%s",\n  "commit": "%s",\n  "source": "%s"\n}\n' "$release_tag" "$commit" "$source_path" > "$staging/release.json"
  chmod -R go-rwx "$staging"
  mv "$staging" "$destination"
  trap - EXIT
fi

pending_link="$install_root/.current-${release_id}.tmp"
ln -s "$destination" "$pending_link"
mv -Tf "$pending_link" "$install_root/current"
printf '%s\n' "$destination/release.json"
