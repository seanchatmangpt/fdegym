"""GymAct-compatible FDE provider over provider-grounded cloud topology.

No real cloud API is mutated here. DO capabilities mutate only the bounded training
world and are marked consequential so ProductionGymAct can keep BRCE as the exclusive
DO path. Real-cloud adapters belong in separate authorized providers.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .catalog import (
    CAPABILITY_FAMILIES,
    CONTROL_DOMAINS,
    PROTOCOLS,
    base_space,
    score_assessment,
)
from .scenarios import get_scenario


@dataclass(frozen=True, slots=True)
class TopologyView:
    provider: str
    regions: tuple[str, ...]
    services: tuple[str, ...]
    source_url: str
    source_version: str | None = None
    fetched_at: str | None = None


def load_gymact_topology(provider: str) -> TopologyView:
    """Load the real GymAct topology or fail with a typed dependency boundary."""
    try:
        from gymact.gyms.cloud_topology import load_topology
    except ImportError as exc:
        raise RuntimeError("UNSUPPORTED:GYMACT_RUNTIME_NOT_INSTALLED") from exc
    topology = load_topology(provider)
    return TopologyView(
        provider=topology.provider,
        regions=tuple(topology.region_codes()),
        services=tuple(topology.service_names()),
        source_url=topology.source_url,
        source_version=topology.source_version,
        fetched_at=topology.fetched_at,
    )


_CAPABILITY_SPECS = (
    ("architecture_doctor", "Explain current FDE architecture gaps and lawful next transitions", "READ"),
    ("list_dimensions", "List DFCM dimensions and cardinalities", "READ"),
    ("enumerate_possibilities", "Enumerate a bounded deterministic page of the lazy DFCM graph", "READ"),
    ("list_regions", "List provider-grounded cloud regions", "READ"),
    ("list_services", "List provider-grounded cloud services", "READ"),
    ("inspect_scenario", "Inspect mission, controls, failures, and evidence obligations", "READ"),
    ("score_assessment", "Apply D1-D8 FDE assessment gates to evidence-backed supplied scores", "READ"),
    ("select_candidate", "Select one reversible candidate in the bounded FDE world", "DO"),
    ("deploy_simulated", "Deploy the selected candidate into the bounded simulated world", "DO"),
    ("apply_control", "Apply a named enterprise control to the bounded world", "DO"),
    ("inject_failure", "Inject an admitted scenario failure into the bounded world", "DO"),
    ("recover", "Recover the bounded world from its current injected failure", "DO"),
    ("rollback", "Rollback simulated deployment to the pre-deployment state", "DO"),
)


def capability_specs() -> tuple[tuple[str, str, str], ...]:
    return _CAPABILITY_SPECS


class FDEEnvironment:
    def __init__(self, *, provider: str, scenario: str, topology: TopologyView | None = None) -> None:
        self.environment_id = f"urn:fdegym:environment:{uuid4().hex}"
        self.requires_authority = True
        self.provider = provider
        self.scenario = get_scenario(scenario)
        self.topology = topology or load_gymact_topology(provider)
        if not self.topology.regions or not self.topology.services:
            raise RuntimeError("UNSUPPORTED:EMPTY_PROVIDER_TOPOLOGY")
        self.space = base_space(regions=self.topology.regions, services=self.topology.services)
        self._closed = False
        self._state: dict[str, Any] = {
            "provider": provider,
            "scenario": scenario,
            "topology_source": self.topology.source_url,
            "topology_source_version": self.topology.source_version,
            "topology_fetched_at": self.topology.fetched_at,
            "region_count": len(self.topology.regions),
            "service_count": len(self.topology.services),
            "possibility_graph_digest": self.space.graph_digest,
            "possibility_cardinality": self.space.cardinality,
            "selected_candidate": None,
            "deployment_status": "NOT_DEPLOYED",
            "controls": [],
            "active_failure": None,
            "recoveries": 0,
            "last_action": "materialized",
        }
        self._pre_deploy_checkpoint: dict[str, Any] | None = None

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("environment is torn down")

    def capabilities(self) -> tuple[Any, ...]:
        self._ensure_open()
        try:
            from gymact.models import Capability, Consequence
        except ImportError as exc:
            raise RuntimeError("UNSUPPORTED:GYMACT_RUNTIME_NOT_INSTALLED") from exc
        return tuple(
            Capability(
                iri=f"urn:fdegym:capability:{binding}",
                title=title,
                consequence=Consequence.READ if consequence == "READ" else Consequence.DO,
                binding=binding,
            )
            for binding, title, consequence in _CAPABILITY_SPECS
        )

    async def observe(self) -> dict[str, Any]:
        self._ensure_open()
        return deepcopy(self._state)

    def _doctor(self) -> dict[str, Any]:
        selected = self._state["selected_candidate"]
        scenario = self.scenario
        controls = set(self._state["controls"])
        missing_controls = [c for c in scenario.required_controls if c not in controls]
        blockers: list[str] = []
        if selected is None:
            blockers.append("NO_CANDIDATE_SELECTED")
        if self._state["deployment_status"] != "DEPLOYED":
            blockers.append("SIMULATED_DEPLOYMENT_NOT_VERIFIED")
        if missing_controls:
            blockers.append("REQUIRED_CONTROLS_MISSING")
        if self._state["active_failure"] is not None:
            blockers.append("ACTIVE_FAILURE")
        return {
            "scenario": scenario.slug,
            "blockers": blockers,
            "missing_controls": missing_controls,
            "ready_for_handoff": not blockers,
            "claim_ceiling": "PARTIAL_ALIVE" if not blockers else "CANDIDATE",
        }

    async def actuate(self, capability: Any, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_open()
        before = deepcopy(self._state)
        binding = capability.binding
        result: Any = None
        if binding == "architecture_doctor":
            result = self._doctor()
        elif binding == "list_dimensions":
            result = {d.name: len(d.values) for d in self.space.dimensions}
        elif binding == "enumerate_possibilities":
            page = self.space.page(
                offset=int(payload.get("offset", 0)),
                limit=int(payload.get("limit", 25)),
                filters=payload.get("filters"),
            )
            result = {
                "total": page.total,
                "offset": page.offset,
                "limit": page.limit,
                "graph_digest": page.graph_digest,
                "candidates": [
                    {
                        "ordinal": c.ordinal,
                        "possibility_id": c.possibility_id,
                        "assignment": dict(c.assignment),
                    }
                    for c in page.candidates
                ],
            }
        elif binding == "list_regions":
            result = list(self.topology.regions)
        elif binding == "list_services":
            result = list(self.topology.services)
        elif binding == "inspect_scenario":
            result = {
                "slug": self.scenario.slug,
                "title": self.scenario.title,
                "mission": self.scenario.mission,
                "required_families": list(self.scenario.required_families),
                "required_protocols": list(self.scenario.required_protocols),
                "required_controls": list(self.scenario.required_controls),
                "injected_failures": list(self.scenario.injected_failures),
                "evidence_obligations": list(self.scenario.evidence_obligations),
            }
        elif binding == "score_assessment":
            scores = payload.get("domain_scores")
            failures = payload.get("unresolved_critical_failures", [])
            if not isinstance(scores, dict) or not isinstance(failures, list):
                raise ValueError("domain_scores must be an object and unresolved_critical_failures a list")
            decision = score_assessment(
                scores, unresolved_critical_failures=tuple(str(item) for item in failures)
            )
            result = {
                "weighted_score": decision.weighted_score,
                "all_domains_at_least_70": decision.all_domains_at_least_70,
                "critical_domains_at_least_80": decision.critical_domains_at_least_80,
                "unresolved_critical_failures": list(decision.unresolved_critical_failures),
                "decision": decision.decision,
            }
        elif binding == "select_candidate":
            assignment = dict(payload.get("assignment") or {})
            required = {"region", "service", "capability_family", "protocol"}
            missing = sorted(required - assignment.keys())
            if missing:
                raise ValueError(f"candidate missing required dimensions: {missing}")
            if assignment["region"] not in self.topology.regions:
                raise ValueError("candidate region is not in grounded provider topology")
            if assignment["service"] not in self.topology.services:
                raise ValueError("candidate service is not in grounded provider topology")
            if assignment["capability_family"] not in CAPABILITY_FAMILIES:
                raise ValueError("candidate capability_family is unknown")
            if assignment["protocol"] not in PROTOCOLS:
                raise ValueError("candidate protocol is unknown")
            self._state["selected_candidate"] = assignment
            self._state["last_action"] = "select_candidate"
            result = assignment
        elif binding == "deploy_simulated":
            if self._state["selected_candidate"] is None:
                raise ValueError("NO_CANDIDATE_SELECTED")
            if self._state["active_failure"] is not None:
                raise ValueError("ACTIVE_FAILURE_BLOCKS_DEPLOYMENT")
            self._pre_deploy_checkpoint = deepcopy(before)
            self._state["deployment_status"] = "DEPLOYED"
            self._state["last_action"] = "deploy_simulated"
            result = {"deployment_status": "DEPLOYED"}
        elif binding == "apply_control":
            control = payload.get("control")
            if control not in CONTROL_DOMAINS:
                raise ValueError("unknown control")
            if control not in self._state["controls"]:
                self._state["controls"].append(control)
                self._state["controls"].sort()
            self._state["last_action"] = "apply_control"
            result = {"control": control}
        elif binding == "inject_failure":
            failure = payload.get("failure")
            if failure not in self.scenario.injected_failures:
                raise ValueError("failure is not admitted by this scenario")
            if self._state["active_failure"] is not None:
                raise ValueError("FAILURE_ALREADY_ACTIVE")
            self._state["active_failure"] = failure
            self._state["deployment_status"] = "DEGRADED"
            self._state["last_action"] = "inject_failure"
            result = {"failure": failure}
        elif binding == "recover":
            if self._state["active_failure"] is None:
                raise ValueError("NO_ACTIVE_FAILURE")
            recovered = self._state["active_failure"]
            self._state["active_failure"] = None
            self._state["recoveries"] += 1
            self._state["deployment_status"] = (
                "DEPLOYED" if self._state["selected_candidate"] is not None else "NOT_DEPLOYED"
            )
            self._state["last_action"] = "recover"
            result = {"recovered": recovered}
        elif binding == "rollback":
            if self._pre_deploy_checkpoint is None:
                raise ValueError("NO_DEPLOYMENT_CHECKPOINT")
            preserved_recoveries = self._state["recoveries"]
            self._state = deepcopy(self._pre_deploy_checkpoint)
            self._state["recoveries"] = preserved_recoveries
            self._state["deployment_status"] = "ROLLED_BACK"
            self._state["last_action"] = "rollback"
            result = {"deployment_status": "ROLLED_BACK"}
        else:
            raise ValueError(f"unsupported fdegym binding: {binding}")
        return {"before": before, "after": deepcopy(self._state), "result": result}

    async def verify(self, expected: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        self._ensure_open()
        observed = await self.observe()
        return all(observed.get(k) == v for k, v in expected.items()), observed

    async def checkpoint(self) -> dict[str, Any]:
        self._ensure_open()
        return deepcopy(self._state)

    async def restore(self, checkpoint: dict[str, Any]) -> None:
        self._ensure_open()
        self._state = deepcopy(checkpoint)

    async def teardown(self) -> None:
        self._closed = True


class FDEProvider:
    name = "fde"
    materialization_requires_authority = False

    async def materialize(self, *, scenario: str | None, config: dict[str, Any]) -> FDEEnvironment:
        scenario_slug = scenario or config.get("scenario", "global-identity")
        provider = config.get("cloud_provider", "aws")
        if not isinstance(scenario_slug, str) or not isinstance(provider, str):
            raise TypeError("scenario and cloud_provider must be strings")
        return FDEEnvironment(provider=provider, scenario=scenario_slug)


def register_with(runtime: Any) -> Any:
    runtime.register_provider(FDEProvider())
    return runtime
