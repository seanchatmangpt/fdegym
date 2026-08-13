from fdegym.dfcm import Dimension
from fdegym.operations import (
    OperationPossibilitySpace,
    cloudsim_operation_payload,
    load_operation_coverage,
    manifest_operation_coverage,
)


def test_ragged_operation_space_preserves_service_operation_topology() -> None:
    coverage = manifest_operation_coverage(
        provider="fixture",
        source="fixture://operation-catalog",
        source_version="1",
        operations_by_service={
            "alpha": ("Create", "Delete"),
            "beta": ("Invoke",),
        },
    )
    space = OperationPossibilitySpace(
        regions=("r1", "r2"),
        coverage=coverage,
        dimensions=(Dimension("protocol", ("HTTP/2", "gRPC")),),
    )
    assert space.cardinality == 12
    observed = [
        dict(item.assignment) for item in space.page(offset=0, limit=7).candidates
    ]
    assert observed[0] == {
        "region": "r1",
        "service": "alpha",
        "operation": "Create",
        "protocol": "HTTP/2",
    }
    assert observed[4]["service"] == "beta"
    assert observed[6]["region"] == "r2"


def test_unsupported_provider_operation_catalog_is_typed_not_invented() -> None:
    coverage = load_operation_coverage(
        "azure", services=("compute", "storage")
    )
    assert coverage.standing == "UNSUPPORTED"
    assert coverage.operation_count == 0
    assert coverage.unknown_services == ("compute", "storage")
    assert (
        coverage.reason
        == "UNSUPPORTED:AZURE_OPERATION_CATALOG_NOT_GROUNDED"
    )


def test_cloudsim_payload_matches_generic_operation_contract() -> None:
    payload = cloudsim_operation_payload(
        {
            "region": "us-east-1",
            "service": "s3",
            "operation": "PutObject",
        },
        effect="CREATE",
        resource_type="object",
        name="artifact",
        properties={"bucket": "example"},
    )
    assert payload["service"] == "s3"
    assert payload["operation"] == "PutObject"
    assert payload["effect"] == "CREATE"
    assert payload["properties"] == {"bucket": "example"}
