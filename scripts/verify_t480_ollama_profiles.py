#!/usr/bin/env python3
"""Compare the static T480 profiles to a loopback Ollama model inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
PROFILES_PATH = ROOT / "catalogue" / "t480-ollama-model-profiles.json"
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:11434/api/tags", help="Loopback Ollama /api/tags URL")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS or parsed.path != "/api/tags":
        print("Refusing non-loopback or non-/api/tags URL.", file=sys.stderr)
        return 2
    try:
        profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))["profiles"]
        with urlopen(args.url, timeout=10) as response:  # nosec B310: URL is restricted above
            inventory = json.load(response)["models"]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Could not read local Ollama inventory: {error}", file=sys.stderr)
        return 1

    installed = {item.get("model"): item for item in inventory if isinstance(item, dict)}
    issues: list[str] = []
    for profile in profiles:
        model = profile["ollama_model"]
        current = installed.get(model)
        if current is None:
            issues.append(f"{profile['id']}: {model} is not installed")
            continue
        details = current.get("details", {})
        for label, expected, actual in (
            ("digest", profile["digest"], current.get("digest")),
            ("size_bytes", profile["size_bytes"], current.get("size")),
            ("parameters", profile["parameters"], details.get("parameter_size")),
            ("quantization", profile["quantization"], details.get("quantization_level")),
        ):
            if expected != actual:
                issues.append(f"{profile['id']}: {label} expected {expected!r}, got {actual!r}")
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    print(f"OK: {len(profiles)} T480 Ollama profiles match exact local digests, sizes, and model details.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
