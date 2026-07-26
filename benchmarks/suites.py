"""Aggregate compatible campaigns across multiple benchmark tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from agent_scope_guard.evidence import EvidenceError, resolve_repository_path
from benchmarks.attempts import AttemptError
from benchmarks.campaigns import (
    CampaignError,
    _aggregate,
    build_campaign_result,
)
from benchmarks.runner import BenchmarkError


class SuiteError(ValueError):
    """Raised when a multi-task suite manifest is invalid."""


def _load_suite(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SuiteError(f"cannot read suite manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SuiteError(
            f"invalid suite JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise SuiteError("suite manifest must contain a JSON object")
    if set(value) != {"schema_version", "suite_id", "campaigns"}:
        raise SuiteError(
            "suite manifest must contain schema_version, suite_id, campaigns"
        )
    if (
        isinstance(value["schema_version"], bool)
        or value["schema_version"] != 1
    ):
        raise SuiteError("schema_version must be 1")
    if not isinstance(value["suite_id"], str) or not value["suite_id"].strip():
        raise SuiteError("suite_id must be a non-empty string")

    campaigns = value["campaigns"]
    if not isinstance(campaigns, list) or not campaigns:
        raise SuiteError("campaigns must be a non-empty array")
    identifiers: set[str] = set()
    paths: set[str] = set()
    for index, item in enumerate(campaigns):
        if not isinstance(item, dict) or set(item) != {"id", "campaign"}:
            raise SuiteError(
                f"campaigns[{index}] must contain id and campaign"
            )
        identifier = item["id"]
        campaign = item["campaign"]
        if not isinstance(identifier, str) or not identifier.strip():
            raise SuiteError(f"campaigns[{index}].id must be non-empty")
        if not isinstance(campaign, str) or not campaign.strip():
            raise SuiteError(
                f"campaigns[{index}].campaign must be non-empty"
            )
        if identifier in identifiers:
            raise SuiteError(f"duplicate campaign id: {identifier}")
        if campaign in paths:
            raise SuiteError(f"duplicate campaign path: {campaign}")
        identifiers.add(identifier)
        paths.add(campaign)
    return value


def build_suite_result(
    suite_path: str | Path,
    repository_root: str | Path,
) -> dict[str, Any]:
    """Replay campaigns and aggregate attempts by shared configuration."""

    root = Path(repository_root).resolve()
    manifest = resolve_repository_path(root, suite_path, "suite")
    suite = _load_suite(manifest)

    campaign_summaries = []
    attempts = []
    descriptions: dict[str, str] = {}
    configuration_order: list[str] = []
    expected_configurations: set[str] | None = None

    for declared in suite["campaigns"]:
        campaign_path = resolve_repository_path(
            root,
            declared["campaign"],
            "campaign",
        )
        result = build_campaign_result(campaign_path, root)
        current = {
            configuration["id"]: configuration["description"]
            for configuration in result["configurations"]
        }
        if expected_configurations is None:
            expected_configurations = set(current)
            configuration_order = [
                configuration["id"]
                for configuration in result["configurations"]
            ]
            descriptions.update(current)
        elif set(current) != expected_configurations:
            raise SuiteError(
                f"campaign {declared['id']} has incompatible configurations"
            )
        elif any(
            descriptions[identifier] != description
            for identifier, description in current.items()
        ):
            raise SuiteError(
                f"campaign {declared['id']} changes a configuration description"
            )

        campaign_summaries.append(
            {
                "id": declared["id"],
                "campaign_id": result["campaign_id"],
                "campaign_manifest": result["campaign_manifest"],
                "task": result["task"],
                "summary": result["summary"],
            }
        )
        for attempt in result["attempts"]:
            attempts.append(
                {
                    "campaign": declared["id"],
                    "task": result["task"]["path"],
                    **attempt,
                }
            )

    configurations = []
    for identifier in configuration_order:
        matching = [
            attempt
            for attempt in attempts
            if attempt["configuration"] == identifier
        ]
        configurations.append(
            {
                "id": identifier,
                "description": descriptions[identifier],
                "summary": _aggregate(matching),
            }
        )

    return {
        "schema_version": 1,
        "suite_id": suite["suite_id"],
        "suite_manifest": {
            "path": manifest.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        },
        "campaigns": campaign_summaries,
        "attempts": attempts,
        "configurations": configurations,
        "summary": _aggregate(attempts),
    }


def serialize_suite_result(result: Mapping[str, Any]) -> str:
    """Serialize a suite result with stable formatting."""

    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True, help="suite manifest")
    parser.add_argument("--output", required=True, help="result JSON path")
    parser.add_argument("--repo-root", default=".", help="repository root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the result")
    mode.add_argument(
        "--verify",
        action="store_true",
        help="compare a fresh run with the committed result",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        root = Path(args.repo_root).resolve()
        suite = resolve_repository_path(root, args.suite, "suite")
        output = resolve_repository_path(root, args.output, "output")
        result = build_suite_result(suite, root)
        rendered = serialize_suite_result(result)
        if args.write:
            output.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"wrote suite result to {output}")
        elif output.read_text(encoding="utf-8") != rendered:
            print("suite result does not match a fresh run")
            return 1
        else:
            print("suite result matches a fresh run")
        return 0
    except (
        AttemptError,
        BenchmarkError,
        CampaignError,
        EvidenceError,
        SuiteError,
        OSError,
    ) as exc:
        print(f"suite error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
