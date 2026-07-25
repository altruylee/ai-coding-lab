"""Aggregate repeated coding-agent attempts without hiding failed runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
import sys
from typing import Any, Mapping

from agent_scope_guard.evidence import EvidenceError, resolve_repository_path
from benchmarks.attempts import AttemptError, build_attempt_result
from benchmarks.runner import BenchmarkError, _task_hash


class CampaignError(ValueError):
    """Raised when a campaign manifest is invalid."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CampaignError(f"cannot read campaign manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CampaignError(
            f"invalid campaign JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise CampaignError("campaign manifest must contain a JSON object")
    return value


def _require_object(
    value: object,
    label: str,
    fields: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CampaignError(f"{label} must be a JSON object")
    unknown = set(value) - fields
    missing = fields - set(value)
    if unknown:
        raise CampaignError(
            f"unknown {label} field(s): {', '.join(sorted(unknown))}"
        )
    if missing:
        raise CampaignError(
            f"missing {label} field(s): {', '.join(sorted(missing))}"
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CampaignError(f"{label} must be a non-empty string")
    return value


def _parse_campaign(path: Path) -> dict[str, Any]:
    campaign = _require_object(
        _load_object(path),
        "campaign",
        {
            "schema_version",
            "campaign_id",
            "task",
            "configurations",
            "attempts",
        },
    )
    if (
        isinstance(campaign["schema_version"], bool)
        or campaign["schema_version"] != 1
    ):
        raise CampaignError("schema_version must be 1")
    _text(campaign["campaign_id"], "campaign_id")
    _text(campaign["task"], "task")

    configurations = campaign["configurations"]
    if not isinstance(configurations, list) or not configurations:
        raise CampaignError("configurations must be a non-empty array")
    configuration_ids: set[str] = set()
    for index, configuration in enumerate(configurations):
        item = _require_object(
            configuration,
            f"configurations[{index}]",
            {"id", "description"},
        )
        identifier = _text(item["id"], f"configurations[{index}].id")
        _text(
            item["description"],
            f"configurations[{index}].description",
        )
        if identifier in configuration_ids:
            raise CampaignError(f"duplicate configuration id: {identifier}")
        configuration_ids.add(identifier)

    attempts = campaign["attempts"]
    if not isinstance(attempts, list) or not attempts:
        raise CampaignError("attempts must be a non-empty array")
    attempt_paths: set[str] = set()
    used_configurations: set[str] = set()
    for index, attempt in enumerate(attempts):
        item = _require_object(
            attempt,
            f"attempts[{index}]",
            {"configuration", "attempt"},
        )
        configuration = _text(
            item["configuration"],
            f"attempts[{index}].configuration",
        )
        attempt_path = _text(item["attempt"], f"attempts[{index}].attempt")
        if configuration not in configuration_ids:
            raise CampaignError(
                f"attempts[{index}] uses unknown configuration: "
                f"{configuration}"
            )
        if attempt_path in attempt_paths:
            raise CampaignError(f"duplicate attempt path: {attempt_path}")
        attempt_paths.add(attempt_path)
        used_configurations.add(configuration)
    unused = configuration_ids - used_configurations
    if unused:
        raise CampaignError(
            "configuration(s) without attempts: "
            + ", ".join(sorted(unused))
        )
    return campaign


def _aggregate(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    elapsed = [
        attempt["elapsed_ms"]
        for attempt in attempts
        if attempt["elapsed_ms"] is not None
    ]
    return {
        "attempts": len(attempts),
        "solved": sum(1 for attempt in attempts if attempt["solved"]),
        "scoreboard_eligible": sum(
            1 for attempt in attempts if attempt["scoreboard_eligible"]
        ),
        "elapsed_ms": {
            "values": elapsed,
            "median": median(elapsed) if elapsed else None,
            "missing": len(attempts) - len(elapsed),
        },
        "human_interventions": sum(
            attempt["human_interventions"] for attempt in attempts
        ),
        "usage_complete": sum(
            1 for attempt in attempts if attempt["usage_complete"]
        ),
    }


def build_campaign_result(
    campaign_path: str | Path,
    repository_root: str | Path,
) -> dict[str, Any]:
    """Replay every declared attempt and aggregate observed results."""

    root = Path(repository_root).resolve()
    manifest = resolve_repository_path(root, campaign_path, "campaign")
    campaign = _parse_campaign(manifest)
    task = resolve_repository_path(root, campaign["task"], "task")
    task_relative = task.relative_to(root).as_posix()

    attempts: list[dict[str, Any]] = []
    for declared in campaign["attempts"]:
        attempt_path = resolve_repository_path(
            root,
            declared["attempt"],
            "attempt",
        )
        result = build_attempt_result(attempt_path, root)
        if result["task"]["path"] != task_relative:
            raise CampaignError(
                f"attempt {result['attempt_id']} targets a different task"
            )
        attempts.append(
            {
                "attempt_id": result["attempt_id"],
                "configuration": declared["configuration"],
                "attempt_manifest_sha256": result["attempt_manifest"][
                    "sha256"
                ],
                "candidate_sha256": result["candidate"]["sha256"],
                "solved": result["summary"]["solved"],
                "scoreboard_eligible": result["summary"][
                    "scoreboard_eligible"
                ],
                "elapsed_ms": result["execution"]["elapsed_ms"],
                "human_interventions": result["execution"][
                    "human_interventions"
                ],
                "usage_complete": result["summary"]["usage_complete"],
            }
        )

    configuration_results = []
    for configuration in campaign["configurations"]:
        matching = [
            attempt
            for attempt in attempts
            if attempt["configuration"] == configuration["id"]
        ]
        configuration_results.append(
            {
                "id": configuration["id"],
                "description": configuration["description"],
                "summary": _aggregate(matching),
            }
        )

    return {
        "schema_version": 1,
        "campaign_id": campaign["campaign_id"],
        "campaign_manifest": {
            "path": manifest.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        },
        "task": {
            "path": task_relative,
            "sha256": _task_hash(task),
        },
        "attempts": attempts,
        "configurations": configuration_results,
        "summary": _aggregate(attempts),
    }


def serialize_campaign_result(result: Mapping[str, Any]) -> str:
    """Serialize a campaign result with stable formatting."""

    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, help="campaign manifest")
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
        campaign = resolve_repository_path(root, args.campaign, "campaign")
        output = resolve_repository_path(root, args.output, "output")
        result = build_campaign_result(campaign, root)
        rendered = serialize_campaign_result(result)
        if args.write:
            output.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"wrote campaign result to {output}")
        elif output.read_text(encoding="utf-8") != rendered:
            print("campaign result does not match a fresh run")
            return 1
        else:
            print("campaign result matches a fresh run")
        return 0
    except (
        AttemptError,
        BenchmarkError,
        CampaignError,
        EvidenceError,
        OSError,
    ) as exc:
        print(f"campaign error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
