"""Admission boundary for externally grounded cloud operation manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .operations import OperationCoverage, manifest_operation_coverage


@dataclass(frozen=True, slots=True)
class AdmittedOperationManifest:
    coverage: OperationCoverage
    artifact_digest: str
    path: str


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"manifest field {key!r} must be a non-empty string")
    return value


def load_operation_manifest(path: str | Path) -> AdmittedOperationManifest:
    """Parse and structurally admit a source-attributed operation manifest.

    Structural admission does not prove the external source is authoritative. The caller
    must separately establish that source/version identity before allowing execution.
    """
    manifest_path = Path(path)
    raw = manifest_path.read_bytes()
    artifact_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("operation manifest root must be an object")

    provider = _require_string(payload, "provider")
    source = _require_string(payload, "source")
    source_version = payload.get("source_version")
    if source_version is not None and not isinstance(source_version, str):
        raise ValueError("source_version must be a string or null")

    services = payload.get("services")
    if not isinstance(services, dict) or not services:
        raise ValueError("services must be a non-empty object")
    normalized: dict[str, tuple[str, ...]] = {}
    for service, operations in services.items():
        if not isinstance(service, str) or not service:
            raise ValueError("service names must be non-empty strings")
        if not isinstance(operations, list) or not operations:
            raise ValueError(f"service {service!r} must have a non-empty operation list")
        if any(not isinstance(item, str) or not item for item in operations):
            raise ValueError(f"service {service!r} has an invalid operation name")
        normalized[service] = tuple(operations)

    coverage = manifest_operation_coverage(
        provider=provider,
        source=source,
        source_version=source_version,
        operations_by_service=normalized,
    )
    return AdmittedOperationManifest(
        coverage=coverage,
        artifact_digest=artifact_digest,
        path=str(manifest_path),
    )
