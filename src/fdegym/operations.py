"""Operation-level cloud surface for maximal, source-bounded DFCM exploration."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from dataclasses import dataclass
from math import prod
from typing import Any

from .dfcm import Candidate, Dimension, PossibilityPage

CLOUD_EFFECTS = (
    "CREATE",
    "UPDATE",
    "DELETE",
    "BIND",
    "UNBIND",
    "TRANSITION",
    "INVOKE",
)


@dataclass(frozen=True, slots=True)
class OperationCoverage:
    provider: str
    source: str
    source_version: str | None
    standing: str
    operations_by_service: dict[str, tuple[str, ...]]
    unknown_services: tuple[str, ...] = ()
    reason: str | None = None

    @property
    def service_count(self) -> int:
        return len(self.operations_by_service)

    @property
    def operation_count(self) -> int:
        return sum(len(items) for items in self.operations_by_service.values())

    @property
    def digest(self) -> str:
        payload = {
            "provider": self.provider,
            "source": self.source,
            "source_version": self.source_version,
            "operations_by_service": self.operations_by_service,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def manifest_operation_coverage(
    *,
    provider: str,
    source: str,
    source_version: str | None,
    operations_by_service: dict[str, tuple[str, ...]],
) -> OperationCoverage:
    """Admit an externally grounded provider operation manifest."""
    if not provider or not source:
        raise ValueError("provider and source must be non-empty")
    normalized: dict[str, tuple[str, ...]] = {}
    for service, operations in sorted(operations_by_service.items()):
        if not service or not operations:
            raise ValueError("every service must have at least one operation")
        unique = tuple(sorted(set(operations)))
        if any(not item for item in unique):
            raise ValueError("operation names must be non-empty")
        normalized[service] = unique
    return OperationCoverage(
        provider=provider,
        source=source,
        source_version=source_version,
        standing="ALIVE",
        operations_by_service=normalized,
    )


def load_operation_coverage(
    provider: str, *, services: tuple[str, ...] | None = None
) -> OperationCoverage:
    """Load operation identities only from an authoritative installed source."""
    if provider != "aws":
        return OperationCoverage(
            provider=provider,
            source="none",
            source_version=None,
            standing="UNSUPPORTED",
            operations_by_service={},
            unknown_services=tuple(sorted(services or ())),
            reason=f"UNSUPPORTED:{provider.upper()}_OPERATION_CATALOG_NOT_GROUNDED",
        )
    try:
        import botocore
        import botocore.session
    except ImportError:
        return OperationCoverage(
            provider="aws",
            source="botocore",
            source_version=None,
            standing="UNSUPPORTED",
            operations_by_service={},
            unknown_services=tuple(sorted(services or ())),
            reason="UNSUPPORTED:AWS_OPERATION_CATALOG_REQUIRES_BOTOCORE",
        )

    session = botocore.session.get_session()
    available = tuple(sorted(session.get_available_services()))
    requested = tuple(sorted(set(services or available)))
    available_set = set(available)
    operations: dict[str, tuple[str, ...]] = {}
    unknown: list[str] = []
    for service in requested:
        if service not in available_set:
            unknown.append(service)
            continue
        model = session.get_service_model(service)
        operations[service] = tuple(sorted(model.operation_names))
    return OperationCoverage(
        provider="aws",
        source="botocore-service-models",
        source_version=getattr(botocore, "__version__", None),
        standing="ALIVE" if operations else "UNSUPPORTED",
        operations_by_service=operations,
        unknown_services=tuple(unknown),
        reason=None if operations else "UNSUPPORTED:NO_AWS_SERVICE_MODELS_ADMITTED",
    )


class OperationPossibilitySpace:
    """Lazy ragged service->operation graph tensored with ordinary DFCM dimensions."""

    def __init__(
        self,
        *,
        regions: tuple[str, ...],
        coverage: OperationCoverage,
        dimensions: tuple[Dimension, ...],
    ) -> None:
        if coverage.standing != "ALIVE":
            raise ValueError("operation coverage must be ALIVE before enumeration")
        if not regions:
            raise ValueError("operation space requires at least one region")
        self.regions = regions
        self.coverage = coverage
        self.dimensions = dimensions
        self._services = tuple(sorted(coverage.operations_by_service))
        cumulative = 0
        prefixes: list[int] = []
        for service in self._services:
            cumulative += len(coverage.operations_by_service[service])
            prefixes.append(cumulative)
        self._operation_prefixes = tuple(prefixes)
        self._operations_per_region = cumulative
        self._tail_width = prod(len(item.values) for item in dimensions) if dimensions else 1

    @property
    def cardinality(self) -> int:
        return len(self.regions) * self._operations_per_region * self._tail_width

    @property
    def graph_digest(self) -> str:
        payload = {
            "regions": self.regions,
            "coverage_digest": self.coverage.digest,
            "dimensions": [(item.name, item.values) for item in self.dimensions],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return f"sha256:{hashlib.sha256(raw).hexdigest()}"

    def _edge(self, edge_ordinal: int) -> tuple[str, str, str]:
        region_index, operation_index = divmod(
            edge_ordinal, self._operations_per_region
        )
        service_index = bisect_right(self._operation_prefixes, operation_index)
        previous = 0 if service_index == 0 else self._operation_prefixes[service_index - 1]
        service = self._services[service_index]
        operation = self.coverage.operations_by_service[service][
            operation_index - previous
        ]
        return self.regions[region_index], service, operation

    def _tail(self, ordinal: int) -> dict[str, str]:
        values: dict[str, str] = {}
        remainder = ordinal
        for dimension in reversed(self.dimensions):
            radix = len(dimension.values)
            values[dimension.name] = dimension.values[remainder % radix]
            remainder //= radix
        return {item.name: values[item.name] for item in self.dimensions}

    def page(self, *, offset: int = 0, limit: int = 25) -> PossibilityPage:
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        stop = min(self.cardinality, offset + limit)
        candidates: list[Candidate] = []
        for ordinal in range(offset, stop):
            edge_ordinal, tail_ordinal = divmod(ordinal, self._tail_width)
            region, service, operation = self._edge(edge_ordinal)
            assignment = {
                "region": region,
                "service": service,
                "operation": operation,
                **self._tail(tail_ordinal),
            }
            raw = json.dumps(
                assignment, sort_keys=True, separators=(",", ":")
            ).encode()
            possibility_id = hashlib.sha256(raw).hexdigest()[:24]
            candidates.append(Candidate(ordinal, possibility_id, assignment))
        return PossibilityPage(
            self.cardinality,
            offset,
            limit,
            self.graph_digest,
            tuple(candidates),
        )


def cloudsim_operation_payload(
    assignment: dict[str, str],
    *,
    effect: str = "INVOKE",
    scope: str = "prod",
    resource_type: str = "resource",
    name: str = "fdegym-operation",
    resource_id: str | None = None,
    properties: dict[str, Any] | None = None,
    depends_on: tuple[str, ...] = (),
    visibility_delay: int = 0,
) -> dict[str, Any]:
    """CONSTRUCT a GymAct CloudSim operation payload; this function never actuates."""
    if effect not in CLOUD_EFFECTS:
        raise ValueError(f"effect must be one of {CLOUD_EFFECTS}")
    required = ("service", "operation", "region")
    missing = [key for key in required if not assignment.get(key)]
    if missing:
        raise ValueError(f"operation assignment missing {missing}")
    if visibility_delay < 0:
        raise ValueError("visibility_delay must be non-negative")
    return {
        "service": assignment["service"],
        "operation": assignment["operation"],
        "effect": effect,
        "scope": scope,
        "region": assignment["region"],
        "resource_type": resource_type,
        "name": name,
        "resource_id": resource_id,
        "properties": dict(properties or {}),
        "depends_on": list(depends_on),
        "visibility_delay": visibility_delay,
    }
