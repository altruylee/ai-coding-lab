"""Run Experiment 001 and produce a deterministic evidence artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_scope_guard.policy import evaluate_paths, load_policy


EXPERIMENT_DIR = Path(__file__).resolve().parent
CASES_PATH = EXPERIMENT_DIR / "cases.json"
POLICY_PATH = EXPERIMENT_DIR / "policy.json"
RESULTS_PATH = EXPERIMENT_DIR / "results.json"


def _load_cases() -> list[dict[str, Any]]:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("cases.json must contain a JSON array")
    return data


def run_experiment() -> dict[str, Any]:
    """Evaluate all declared cases and return a deterministic result."""

    policy = load_policy(POLICY_PATH)
    case_results: list[dict[str, Any]] = []

    for case in _load_cases():
        violations = evaluate_paths(policy, case["changed_paths"])
        observed_codes = [violation.code for violation in violations]
        expected_codes = list(case["expected_codes"])
        case_results.append(
            {
                "id": case["id"],
                "description": case["description"],
                "changed_paths": list(case["changed_paths"]),
                "expected_codes": expected_codes,
                "observed_codes": observed_codes,
                "passed": observed_codes == expected_codes,
            }
        )

    passed = sum(1 for case in case_results if case["passed"])
    return {
        "experiment_id": "001-scope-boundaries",
        "question": (
            "Can scope policy distinguish allowed changes, out-of-scope files, "
            "missing tests, and sensitive key files?"
        ),
        "summary": {
            "cases": len(case_results),
            "passed": passed,
            "failed": len(case_results) - passed,
        },
        "cases": case_results,
    }


def _serialized(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="replace results.json with the current deterministic result",
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="verify the current result matches results.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_experiment()
    rendered = _serialized(result)

    if args.write:
        RESULTS_PATH.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {RESULTS_PATH.relative_to(REPOSITORY_ROOT)}")
    elif args.verify:
        committed = RESULTS_PATH.read_text(encoding="utf-8")
        if committed != rendered:
            print("results.json does not match a fresh experiment run", file=sys.stderr)
            return 1
        print("experiment result matches the committed evidence")
    else:
        print(rendered, end="")

    return 0 if result["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
