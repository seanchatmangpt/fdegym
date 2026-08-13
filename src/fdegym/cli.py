"""Dependency-light CLI; GymAct is imported only for runtime probes."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from typing import Any

from .catalog import summary
from .provider import FDEProvider, load_gymact_topology
from .scenarios import SCENARIOS


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def cmd_catalog(_: argparse.Namespace) -> int:
    _print(asdict(summary()))
    return 0


def cmd_scenarios(_: argparse.Namespace) -> int:
    _print([{"slug": s.slug, "title": s.title, "mission": s.mission} for s in SCENARIOS])
    return 0


def cmd_topology(args: argparse.Namespace) -> int:
    topology = load_gymact_topology(args.provider)
    _print(
        {
            "provider": topology.provider,
            "regions": len(topology.regions),
            "services": len(topology.services),
            "source_url": topology.source_url,
            "source_version": topology.source_version,
            "fetched_at": topology.fetched_at,
        }
    )
    return 0


async def _probe(args: argparse.Namespace) -> dict[str, Any]:
    try:
        from gymact.models import MaterializationIntent
        from gymact.runtime import ProductionGymAct
    except ImportError as exc:
        raise RuntimeError("UNSUPPORTED:GYMACT_RUNTIME_NOT_INSTALLED") from exc
    runtime = ProductionGymAct()
    runtime.register_provider(FDEProvider())
    result = await runtime.materialize(
        MaterializationIntent(
            provider="fde",
            scenario=args.scenario,
            config={"cloud_provider": args.provider},
            idempotency_key=f"fdegym-probe:{args.provider}:{args.scenario}",
        )
    )
    return result.model_dump(mode="json")


def cmd_probe(args: argparse.Namespace) -> int:
    _print(asyncio.run(_probe(args)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fdegym")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("catalog", help="show cross-provider DFCM catalog size")
    p.set_defaults(func=cmd_catalog)
    p = sub.add_parser("scenarios", help="list Fortune-5 FDE scenarios")
    p.set_defaults(func=cmd_scenarios)
    p = sub.add_parser("topology", help="summarize a GymAct provider-grounded topology")
    p.add_argument("--provider", choices=("aws", "azure", "gcp"), default="aws")
    p.set_defaults(func=cmd_topology)
    p = sub.add_parser("probe", help="materialize the FDE provider through ProductionGymAct")
    p.add_argument("--provider", choices=("aws", "azure", "gcp"), default="aws")
    p.add_argument("--scenario", default="global-identity")
    p.set_defaults(func=cmd_probe)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (RuntimeError, ValueError, KeyError) as exc:
        _print({"standing": "UNSUPPORTED" if "UNSUPPORTED:" in str(exc) else "BLOCKED", "reason": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
