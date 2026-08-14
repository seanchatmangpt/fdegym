import json

import pytest

from fdegym.operation_manifest import load_operation_manifest


def test_operation_manifest_binds_source_version_and_artifact_digest(tmp_path) -> None:
    path = tmp_path / "operations.json"
    path.write_text(
        json.dumps(
            {
                "provider": "future-cloud",
                "source": "https://example.invalid/authoritative-api-model",
                "source_version": "2026-08-13",
                "services": {
                    "compute": ["Create", "Delete", "Create"],
                    "storage": ["Put", "Get"],
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    admitted = load_operation_manifest(path)
    assert admitted.artifact_digest.startswith("sha256:")
    assert admitted.coverage.provider == "future-cloud"
    assert admitted.coverage.source_version == "2026-08-13"
    assert admitted.coverage.operations_by_service["compute"] == (
        "Create",
        "Delete",
    )


def test_operation_manifest_refuses_missing_source(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps(
            {
                "provider": "future-cloud",
                "services": {"compute": ["Create"]},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="source"):
        load_operation_manifest(path)
