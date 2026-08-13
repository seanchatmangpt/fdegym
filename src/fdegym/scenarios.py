"""Fortune-5 forward-deployment scenario portfolio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Scenario:
    slug: str
    title: str
    mission: str
    required_families: tuple[str, ...]
    required_protocols: tuple[str, ...]
    required_controls: tuple[str, ...]
    injected_failures: tuple[str, ...]
    evidence_obligations: tuple[str, ...]


_DEF_EVIDENCE = (
    "admitted-observation",
    "architecture-decision",
    "authority-decision",
    "independent-verification",
    "receipt",
    "replay",
    "maintainer-handoff",
)

SCENARIOS = (
    Scenario(
        "global-identity",
        "Global workforce and customer identity",
        "Unify identity across acquisitions and clouds without creating ambient authority.",
        ("identity-access", "secrets-keys-pki", "integration-api-management", "observability"),
        ("OpenID-Connect", "OAuth2", "SAML2", "SCIM2", "FIDO2-WebAuthn"),
        ("least-privilege", "zero-trust", "audit-logging", "approval-separation-of-duties"),
        ("identity-provider-loss", "credential-revocation", "certificate-expiry"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "regulated-payments",
        "Regulated global payments platform",
        "Operate low-latency payments with regional failure, strong isolation, and auditable recovery.",
        ("compute", "networking", "relational-database", "messaging-eventing", "sre-resilience"),
        ("TLS1.3", "HTTP/2", "gRPC", "Apache-Kafka"),
        ("segmentation", "encryption-at-rest", "audit-logging", "multi-region-recovery"),
        ("region-loss", "database-failover", "queue-backlog", "dependency-outage"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "media-supply-chain",
        "Global media supply chain",
        "Move large media assets through ingest, processing, rights, localization, and distribution.",
        ("storage-object", "batch-hpc", "messaging-eventing", "cdn-edge", "data-lake"),
        ("S3-API", "HTTP/2", "CloudEvents", "OpenTelemetry-OTLP"),
        ("data-classification", "retention-deletion", "software-supply-chain", "cost-allocation"),
        ("storage-unavailable", "queue-backlog", "cost-spike", "bad-deployment"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "enterprise-genai",
        "Governed enterprise GenAI platform",
        "Ship reusable model, RAG, agent, evaluation, observability, and authority boundaries.",
        ("ai-ml", "genai-agents", "data-lake", "identity-access", "observability"),
        ("HTTP/2", "REST", "gRPC", "MCP", "A2A", "OpenTelemetry-OTLP"),
        ("least-privilege", "data-classification", "policy-as-code", "receipt-replay"),
        ("dependency-outage", "quota-exhaustion", "data-corruption", "telemetry-loss"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "zero-downtime-migration",
        "Zero-downtime estate migration",
        "Move a mission-critical estate while preserving business continuity and rollback.",
        ("migration-modernization", "networking", "relational-database", "business-continuity-dr"),
        ("DNS", "BGP", "TLS1.3", "REST"),
        ("backup-restore", "multi-region-recovery", "audit-logging", "receipt-replay"),
        ("network-partition", "database-failover", "bad-deployment", "dns-failure"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "ransomware-recovery",
        "Ransomware containment and recovery",
        "Contain compromise, preserve evidence, restore clean operations, and prove recovery.",
        ("security-posture", "threat-detection", "backup-archive", "business-continuity-dr"),
        ("Syslog", "OpenTelemetry-OTLP", "HTTP/2"),
        ("zero-trust", "key-rotation", "backup-restore", "audit-logging"),
        ("ransomware", "secret-compromise", "telemetry-loss", "identity-provider-loss"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "multi-cloud-sovereignty",
        "Multi-cloud data sovereignty",
        "Preserve workload portability while enforcing regional residency and policy differences.",
        ("policy-governance", "networking", "storage-object", "containers", "kubernetes"),
        ("Kubernetes-API", "OCI-Image", "CNI", "CSI", "OpenID-Connect"),
        ("data-residency", "policy-as-code", "segmentation", "receipt-replay"),
        ("region-loss", "network-partition", "schema-drift", "quota-exhaustion"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "api-ecosystem",
        "Enterprise API and event ecosystem",
        "Standardize synchronous and asynchronous integration without centralizing every implementation.",
        ("integration-api-management", "messaging-eventing", "identity-access", "observability"),
        ("OpenAPI", "AsyncAPI", "REST", "GraphQL", "gRPC", "CloudEvents", "OAuth2"),
        ("least-privilege", "audit-logging", "policy-as-code", "slo-error-budget"),
        ("rate-limit", "schema-drift", "dependency-outage", "telemetry-loss"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "finops-rearchitecture",
        "Enterprise cost and capacity rearchitecture",
        "Reduce structural cloud cost without trading away resilience, security, or operability.",
        ("finops", "compute", "storage-object", "observability", "sre-resilience"),
        ("OpenTelemetry-OTLP", "Prometheus-OpenMetrics", "REST"),
        ("cost-allocation", "capacity-management", "slo-error-budget", "receipt-replay"),
        ("cost-spike", "quota-exhaustion", "region-loss"),
        _DEF_EVIDENCE,
    ),
    Scenario(
        "ma-platform-integration",
        "M&A platform integration",
        "Integrate acquired identity, network, data, developer, and governance planes incrementally.",
        ("identity-access", "networking", "data-lake", "devex-cicd", "policy-governance"),
        ("SAML2", "SCIM2", "BGP", "REST", "OCI-Image"),
        ("least-privilege", "segmentation", "data-classification", "software-supply-chain"),
        ("identity-provider-loss", "network-partition", "schema-drift", "supply-chain-compromise"),
        _DEF_EVIDENCE,
    ),
)

SCENARIO_BY_SLUG = {scenario.slug: scenario for scenario in SCENARIOS}


def get_scenario(slug: str) -> Scenario:
    try:
        return SCENARIO_BY_SLUG[slug]
    except KeyError as exc:
        raise KeyError(f"unknown FDE scenario {slug!r}; choose from {sorted(SCENARIO_BY_SLUG)}") from exc
