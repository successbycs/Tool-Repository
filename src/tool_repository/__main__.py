from __future__ import annotations

import argparse
from pathlib import Path

from tool_repository.knowledge import load_knowledge_base
from tool_repository.manifest import discover_manifests, load_manifest
from tool_repository.milestones import close_check, validate_registry
from tool_repository.repository_intake import load_queue


def main() -> int:
    parser = argparse.ArgumentParser(prog="tool_repository")
    commands = parser.add_subparsers(dest="command", required=True)
    milestones = commands.add_parser("milestones")
    milestone_commands = milestones.add_subparsers(dest="milestone_command", required=True)
    milestone_commands.add_parser("validate")
    close = milestone_commands.add_parser("close-check")
    close.add_argument("milestone_id")
    validate = commands.add_parser("validate", help="Validate static adapter descriptors without importing adapter code")
    validate.add_argument("paths", nargs="*", type=Path, help="adapter.json files; defaults to adapters/**/adapter.json")
    validate.add_argument("--require-knowledge", action="store_true", help="Validate knowledge records; uses the safe contract fixture while no adapters exist")
    repositories = commands.add_parser("repositories")
    repository_commands = repositories.add_subparsers(dest="repository_command", required=True)
    validate_queue = repository_commands.add_parser("validate-queue", help="Validate the read-only repository intake queue")
    validate_queue.add_argument("--queue", type=Path, default=Path("intake/repository_queue.json"))
    args = parser.parse_args()

    if args.command == "milestones":
        issues = validate_registry() if args.milestone_command == "validate" else close_check(args.milestone_id)
    elif args.command == "validate":
        paths = args.paths or discover_manifests(Path.cwd())
        issues = [issue for path in paths for issue in load_manifest(path, repository_root=Path.cwd())[1]]
        if args.require_knowledge:
            if paths:
                for path in paths:
                    manifest, manifest_issues = load_manifest(path, repository_root=Path.cwd())
                    if manifest is not None and not manifest_issues:
                        knowledge_path = Path.cwd() / manifest["documentation"]["knowledge_base"]
                        issues.extend(load_knowledge_base(knowledge_path, repository_root=Path.cwd(), adapter_id=manifest["adapter"]["id"], adapter_version=manifest["adapter"]["version"])[1])
            else:
                fixture = Path.cwd() / "examples" / "knowledge-base-fixture" / "knowledge.json"
                issues.extend(load_knowledge_base(fixture, repository_root=Path.cwd())[1])
    elif args.command == "repositories":
        _, issues = load_queue(Path.cwd() / args.queue, repository_root=Path.cwd())
    else:  # pragma: no cover - argparse makes this unreachable
        issues = close_check(args.milestone_id)
    if issues:
        print("\n".join(f"ERROR: {issue}" for issue in issues))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
