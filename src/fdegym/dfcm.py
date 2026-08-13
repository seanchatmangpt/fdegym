"""Lazy Design-for-Combinatorial-Maximalism possibility space.

The graph is represented as a product of admitted dimensions and is enumerated by
mixed-radix unranking. The implementation therefore preserves a potentially enormous
reversible space without allocating the Cartesian product.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import prod


@dataclass(frozen=True, slots=True)
class Dimension:
    name: str
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("dimension name must be non-empty")
        if not self.values:
            raise ValueError(f"dimension {self.name!r} must have at least one value")
        if len(set(self.values)) != len(self.values):
            raise ValueError(f"dimension {self.name!r} contains duplicate values")


@dataclass(frozen=True, slots=True)
class Candidate:
    ordinal: int
    possibility_id: str
    assignment: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class PossibilityPage:
    total: int
    offset: int
    limit: int
    graph_digest: str
    candidates: tuple[Candidate, ...]


class PossibilitySpace:
    """A deterministic, lazily enumerable product graph.

    ``graph_digest`` is a construction identity (SHA-256), not a GymAct receipt.
    Once GymAct executes an admitted candidate, GymAct remains responsible for its
    BLAKE3 evidence/receipt chain.
    """

    def __init__(self, dimensions: Sequence[Dimension]) -> None:
        if not dimensions:
            raise ValueError("possibility space requires at least one dimension")
        names = [d.name for d in dimensions]
        if len(set(names)) != len(names):
            raise ValueError("dimension names must be unique")
        self._dimensions = tuple(dimensions)

    @property
    def dimensions(self) -> tuple[Dimension, ...]:
        return self._dimensions

    @property
    def cardinality(self) -> int:
        return prod(len(d.values) for d in self._dimensions)

    @property
    def graph_digest(self) -> str:
        payload = [(d.name, d.values) for d in self._dimensions]
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        return f"sha256:{hashlib.sha256(raw).hexdigest()}"

    def _filtered_dimensions(
        self, filters: Mapping[str, Iterable[str]] | None
    ) -> tuple[Dimension, ...]:
        if not filters:
            return self._dimensions
        known = {d.name for d in self._dimensions}
        unknown = set(filters) - known
        if unknown:
            raise KeyError(f"unknown DFCM dimensions: {sorted(unknown)}")
        out: list[Dimension] = []
        for dimension in self._dimensions:
            requested = filters.get(dimension.name)
            if requested is None:
                out.append(dimension)
                continue
            requested_set = set(requested)
            values = tuple(v for v in dimension.values if v in requested_set)
            if not values:
                raise ValueError(f"filter removes every value from dimension {dimension.name!r}")
            out.append(Dimension(dimension.name, values))
        return tuple(out)

    @staticmethod
    def _candidate_id(assignment: Mapping[str, str]) -> str:
        raw = json.dumps(assignment, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()[:24]

    @staticmethod
    def _unrank(ordinal: int, dimensions: Sequence[Dimension]) -> dict[str, str]:
        total = prod(len(d.values) for d in dimensions)
        if ordinal < 0 or ordinal >= total:
            raise IndexError(f"ordinal {ordinal} outside [0,{total})")
        remainder = ordinal
        indexes = [0] * len(dimensions)
        for i in range(len(dimensions) - 1, -1, -1):
            radix = len(dimensions[i].values)
            indexes[i] = remainder % radix
            remainder //= radix
        return {d.name: d.values[indexes[i]] for i, d in enumerate(dimensions)}

    def page(
        self,
        *,
        offset: int = 0,
        limit: int = 25,
        filters: Mapping[str, Iterable[str]] | None = None,
    ) -> PossibilityPage:
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        dimensions = self._filtered_dimensions(filters)
        total = prod(len(d.values) for d in dimensions)
        stop = min(total, offset + limit)
        candidates = []
        for ordinal in range(offset, stop):
            assignment = self._unrank(ordinal, dimensions)
            candidates.append(Candidate(ordinal, self._candidate_id(assignment), assignment))
        filtered = PossibilitySpace(dimensions)
        return PossibilityPage(total, offset, limit, filtered.graph_digest, tuple(candidates))
