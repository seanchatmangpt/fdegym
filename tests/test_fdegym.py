from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from fdegym.catalog import (
    CAPABILITY_FAMILIES,
    CONTROL_DOMAINS,
    FAILURE_MODES,
    PROTOCOLS,
    base_space,
    summary,
)
from fdegym.dfcm import Dimension, PossibilitySpace
from fdegym.provider import FDEEnvironment, TopologyView
from fdegym.scenarios import SCENARIOS


def test_dfcm_uses_lazy_mixed_radix_enumeration() -> None:
    space = PossibilitySpace((Dimension("a", ("0", "1")), Dimension("b", ("x", "y", "z"))))
    assert space.cardinality == 6
    page = space.page(offset=2, limit=3)
    assert [c.ordinal for c in page.candidates] == [2, 3, 4]
    assert [dict(c.assignment) for c in page.candidates] == [
        {"a": "0", "b": "z"},
        {"a": "1", "b": "x"},
        {"a": "1", "b": "y"},
    ]
    assert len({c.possibility_id for c in page.candidates}) == 3


def test_dfcm_filter_preserves_deterministic_subgraph() -> None:
    space = PossibilitySpace((Dimension("a", ("0", "1")), Dimension("b", ("x", "y"))))
    page = space.page(filters={"a": ["1"]}, limit=10)
    assert page.total == 2
    assert [dict(c.assignment) for c in page.candidates] == [
        {"a": "1", "b": "x"},
        {"a": "1", "b": "y"},
    ]


def test_catalog_is_broad_and_nonduplicative() -> None:
    counts = summary()
    assert counts.capability_families >= 40
    assert counts.protocols >= 60
    assert len(set(PROTOCOLS)) == len(PROTOCOLS)
    assert len(set(CAPABILITY_FAMILIES)) == len(CAPABILITY_FAMILIES)
    assert len(set(CONTROL_DOMAINS)) == len(CONTROL_DOMAINS)
    assert len(set(FAILURE_MODES)) == len(FAILURE_MODES)


def test_provider_topology_multiplies_without_materializing_cartesian_product() -> None:
    space = base_space(regions=("r1", "r2"), services=("s1", "s2", "s3"))
    expected = (
        2
        * 3
        * summary().capability_families
        * summary().protocols
        * summary().roles
        * summary().lifecycle_stages
        * summary().failure_modes
        * summary().control_domains
        * summary().quality_attributes
    )
    assert space.cardinality == expected
    assert len(space.page(limit=2).candidates) == 2


def test_every_scenario_carries_failure_control_and_evidence_obligations() -> None:
    assert len(SCENARIOS) >= 10
    for scenario in SCENARIOS:
        assert scenario.required_families
        assert scenario.required_protocols
        assert scenario.required_controls
        assert scenario.injected_failures
        assert "receipt" in scenario.evidence_obligations
        assert "replay" in scenario.evidence_obligations
        assert set(scenario.required_families) <= set(CAPABILITY_FAMILIES)
        assert set(scenario.required_protocols) <= set(PROTOCOLS)
        assert set(scenario.required_controls) <= set(CONTROL_DOMAINS)
        assert set(scenario.injected_failures) <= set(FAILURE_MODES)


@dataclass(frozen=True)
class _Capability:
    binding: str
    iri: str = "urn:test"


def test_bounded_world_select_deploy_fail_recover_rollback() -> None:
    topology = TopologyView("aws", ("r1",), ("svc",), "fixture://grounded-topology")
    env = FDEEnvironment(provider="aws", scenario="global-identity", topology=topology)
    candidate = {
        "region": "r1",
        "service": "svc",
        "capability_family": "identity-access",
        "protocol": "OpenID-Connect",
    }

    async def run() -> None:
        await env.actuate(_Capability("select_candidate"), {"assignment": candidate})
        await env.actuate(_Capability("deploy_simulated"), {})
        await env.actuate(_Capability("inject_failure"), {"failure": "identity-provider-loss"})
        state = await env.observe()
        assert state["deployment_status"] == "DEGRADED"
        await env.actuate(_Capability("recover"), {})
        state = await env.observe()
        assert state["deployment_status"] == "DEPLOYED"
        assert state["recoveries"] == 1
        await env.actuate(_Capability("rollback"), {})
        state = await env.observe()
        assert state["deployment_status"] == "ROLLED_BACK"

    asyncio.run(run())


def test_unknown_scenario_is_refused() -> None:
    topology = TopologyView("aws", ("r1",), ("svc",), "fixture://grounded-topology")
    with pytest.raises(KeyError):
        FDEEnvironment(provider="aws", scenario="does-not-exist", topology=topology)


def test_assessment_gate_matches_eight_domain_blueprint() -> None:
    from fdegym.catalog import score_assessment

    passing = {f"D{i}": 85.0 for i in range(1, 9)}
    assert score_assessment(passing).decision == "CERTIFY"

    weak_security = dict(passing)
    weak_security["D4"] = 75.0
    assert score_assessment(weak_security).decision == "TARGETED_REASSESSMENT"

    held = score_assessment(passing, unresolved_critical_failures=("CF-01",))
    assert held.decision == "HOLD"
