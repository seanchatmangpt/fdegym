#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tomllib

PLANES = ("semantics", "evaluation", "runtime", "evidence", "operations")
LEVELS = (
    "M0 Seed",
    "M1 Modeled",
    "M2 Admitted",
    "M3 Runnable",
    "M4 Receipted",
    "M5 Replayable",
    "M6 Enterprise",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_manifest(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate(manifest: dict) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    if manifest.get("contract_version") != "1":
        errors.append("contract_version must be 1")
    if manifest.get("gym", {}).get("mode") != "offline_simulation":
        errors.append("gym.mode must be offline_simulation")
    if manifest.get("exercise", {}).get("kind") != "offline_simulation":
        errors.append("exercise.kind must be offline_simulation")
    levels = manifest.get("maturity", {}).get("planes", {})
    for plane in PLANES:
        value = levels.get(plane)
        if not isinstance(value, int) or not 0 <= value <= 6:
            errors.append(f"maturity.planes.{plane} must be an integer from 0 through 6")
    return errors, {plane: int(levels.get(plane, 0)) for plane in PLANES}


def check(manifest: dict) -> int:
    errors, levels = validate(manifest)
    if errors:
        print(json.dumps({"standing": "BLOCKED", "errors": errors}, indent=2))
        return 1
    overall = min(levels.values())
    print(json.dumps({
        "standing": "PARTIAL_ALIVE",
        "overall": LEVELS[overall],
        "planes": {plane: LEVELS[level] for plane, level in levels.items()},
    }, indent=2, sort_keys=True))
    return 0


def evaluate(manifest: dict, out: Path | None) -> int:
    errors, levels = validate(manifest)
    if errors:
        print(json.dumps({"standing": "BLOCKED", "errors": errors}, indent=2))
        return 1
    subject = {
        "gym": manifest["gym"]["name"],
        "exercise": manifest["exercise"]["id"],
        "mode": manifest["gym"]["mode"],
    }
    receipt = {
        "schema": "gym-receipt/v1",
        "standing": "PARTIAL_ALIVE",
        "subject": subject,
        "observed": ["gym.toml"],
        "admitted": [subject],
        "executed": ["offline maturity evaluation"],
        "changed": [],
        "verified": ["manifest shape", "five-plane floor", "deterministic receipt"],
        "inferred": [],
        "refused": [],
        "blocked": [],
        "unsupported": [],
        "overall_level": min(levels.values()),
        "manifest_digest": digest(manifest),
        "subject_digest": digest(subject),
    }
    receipt["receipt_digest"] = digest(receipt)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if out:
        out.write_text(rendered)
    print(rendered, end="")
    return 0


def replay(path: Path) -> int:
    receipt = json.loads(path.read_text())
    claimed = receipt.pop("receipt_digest", None)
    actual = digest(receipt)
    ok = claimed == actual
    print(json.dumps({"replay": "PASS" if ok else "FAIL", "claimed": claimed, "actual": actual}, indent=2))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "evaluate", "replay"))
    parser.add_argument("target", nargs="?", default="gym.toml")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "replay":
        return replay(Path(args.target))
    manifest = load_manifest(Path(args.target))
    return check(manifest) if args.command == "check" else evaluate(manifest, args.out)


if __name__ == "__main__":
    sys.exit(main())
