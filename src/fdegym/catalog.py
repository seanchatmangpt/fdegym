"""Public, extensible FDE capability dimensions.

Provider service names are intentionally *not* copied here. They are loaded from
GymAct's provider-grounded cloud topology adapter at runtime. This file contains only
cross-provider architectural dimensions and standards/profile concepts.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dfcm import Dimension, PossibilitySpace

CAPABILITY_FAMILIES = (
    "compute",
    "virtual-machines",
    "bare-metal",
    "containers",
    "kubernetes",
    "serverless",
    "batch-hpc",
    "networking",
    "load-balancing",
    "dns",
    "cdn-edge",
    "service-mesh",
    "private-connectivity",
    "storage-object",
    "storage-block",
    "storage-file",
    "backup-archive",
    "relational-database",
    "nosql-database",
    "cache",
    "graph-database",
    "search",
    "data-lake",
    "data-warehouse",
    "stream-processing",
    "messaging-eventing",
    "integration-api-management",
    "identity-access",
    "secrets-keys-pki",
    "security-posture",
    "threat-detection",
    "policy-governance",
    "observability",
    "sre-resilience",
    "finops",
    "devex-cicd",
    "artifact-supply-chain",
    "ai-ml",
    "genai-agents",
    "iot-ot",
    "migration-modernization",
    "business-continuity-dr",
)

PROTOCOLS = (
    "IPv4",
    "IPv6",
    "TCP",
    "UDP",
    "ICMP",
    "DNS",
    "DHCP",
    "BGP",
    "OSPF",
    "VXLAN",
    "GRE",
    "IPsec",
    "WireGuard",
    "TLS1.2",
    "TLS1.3",
    "QUIC",
    "HTTP/1.1",
    "HTTP/2",
    "HTTP/3",
    "WebSocket",
    "SSE",
    "REST",
    "GraphQL",
    "gRPC",
    "SOAP",
    "OData",
    "S3-API",
    "NFS",
    "SMB",
    "iSCSI",
    "SFTP",
    "SSH",
    "RDP",
    "SMTP",
    "IMAP",
    "MQTT",
    "AMQP-0-9-1",
    "AMQP-1.0",
    "Apache-Kafka",
    "NATS",
    "CloudEvents",
    "OpenAPI",
    "AsyncAPI",
    "OAuth2",
    "OpenID-Connect",
    "SAML2",
    "SCIM2",
    "FIDO2-WebAuthn",
    "SPIFFE",
    "X.509",
    "JWT",
    "OPA-Rego",
    "Kubernetes-API",
    "OCI-Image",
    "OCI-Runtime",
    "CNI",
    "CSI",
    "WASI",
    "WIT",
    "OpenTelemetry-OTLP",
    "Prometheus-OpenMetrics",
    "Syslog",
    "SNMP",
    "MCP",
    "A2A",
)

FDE_ROLES = (
    "discovery-lead",
    "domain-modeler",
    "enterprise-architect",
    "solution-architect",
    "platform-engineer",
    "cloud-engineer",
    "data-engineer",
    "security-engineer",
    "sre",
    "finops-engineer",
    "migration-lead",
    "incident-commander",
    "customer-enablement",
    "architecture-falsifier",
)

LIFECYCLE_STAGES = (
    "discover",
    "scope",
    "model",
    "design",
    "construct",
    "verify",
    "deploy",
    "adopt",
    "operate",
    "recover",
    "handoff",
    "platformize",
)

FAILURE_MODES = (
    "region-loss",
    "zone-loss",
    "identity-provider-loss",
    "dns-failure",
    "network-partition",
    "packet-loss-latency",
    "certificate-expiry",
    "secret-compromise",
    "credential-revocation",
    "dependency-outage",
    "database-failover",
    "storage-unavailable",
    "queue-backlog",
    "quota-exhaustion",
    "rate-limit",
    "bad-deployment",
    "schema-drift",
    "data-corruption",
    "telemetry-loss",
    "cost-spike",
    "supply-chain-compromise",
    "ransomware",
)

CONTROL_DOMAINS = (
    "least-privilege",
    "zero-trust",
    "segmentation",
    "encryption-in-transit",
    "encryption-at-rest",
    "key-rotation",
    "secrets-management",
    "data-classification",
    "data-residency",
    "retention-deletion",
    "audit-logging",
    "policy-as-code",
    "software-supply-chain",
    "vulnerability-management",
    "threat-detection-response",
    "backup-restore",
    "multi-region-recovery",
    "slo-error-budget",
    "capacity-management",
    "cost-allocation",
    "approval-separation-of-duties",
    "receipt-replay",
)

QUALITY_ATTRIBUTES = (
    "availability",
    "reliability",
    "recoverability",
    "security",
    "privacy",
    "compliance",
    "performance",
    "latency",
    "throughput",
    "scalability",
    "elasticity",
    "maintainability",
    "operability",
    "observability",
    "portability",
    "interoperability",
    "cost-efficiency",
    "sustainability",
)

GYMACT_TOPOLOGY_PROVIDERS = ("aws", "azure", "gcp")
EXTENSION_PROVIDER_TARGETS = (
    "alibaba-cloud",
    "ibm-cloud",
    "oracle-cloud",
    "cloudflare",
    "digitalocean",
    "openstack",
    "vmware-vcf",
    "kubernetes",
)


@dataclass(frozen=True, slots=True)
class CatalogSummary:
    capability_families: int
    protocols: int
    roles: int
    lifecycle_stages: int
    failure_modes: int
    control_domains: int
    quality_attributes: int
    grounded_cloud_providers: int
    extension_targets: int


def summary() -> CatalogSummary:
    return CatalogSummary(
        len(CAPABILITY_FAMILIES),
        len(PROTOCOLS),
        len(FDE_ROLES),
        len(LIFECYCLE_STAGES),
        len(FAILURE_MODES),
        len(CONTROL_DOMAINS),
        len(QUALITY_ATTRIBUTES),
        len(GYMACT_TOPOLOGY_PROVIDERS),
        len(EXTENSION_PROVIDER_TARGETS),
    )


def base_space(*, regions: tuple[str, ...], services: tuple[str, ...]) -> PossibilitySpace:
    """Build the maximal *lazy* architectural graph for one grounded provider."""
    return PossibilitySpace(
        (
            Dimension("region", regions),
            Dimension("service", services),
            Dimension("capability_family", CAPABILITY_FAMILIES),
            Dimension("protocol", PROTOCOLS),
            Dimension("role", FDE_ROLES),
            Dimension("lifecycle_stage", LIFECYCLE_STAGES),
            Dimension("failure_mode", FAILURE_MODES),
            Dimension("control_domain", CONTROL_DOMAINS),
            Dimension("quality_attribute", QUALITY_ATTRIBUTES),
        )
    )

ASSESSMENT_DOMAINS = {
    "D1": "workflow-domain-modeling",
    "D2": "agent-product-architecture",
    "D3": "platform-integration",
    "D4": "authority-security-privacy-governance",
    "D5": "evaluation-reliability",
    "D6": "ai-native-software-manufacturing",
    "D7": "economics-business-outcomes",
    "D8": "leadership-communication-adoption",
}

CRITICAL_FAILURES = {
    "CF-01": "unadmitted-consequential-actuation",
    "CF-02": "fabricated-or-materially-altered-evidence",
    "CF-03": "unattributed-upstream-generated-or-team-contribution",
    "CF-04": "no-meaningful-evaluation",
    "CF-05": "cannot-contain-rollback-or-recover",
    "CF-06": "prohibited-data-exposure",
    "CF-07": "foreseeable-uncontrolled-illegal-or-discriminatory-outcome",
    "CF-08": "claimed-outcome-not-reproducible-or-replayable",
    "CF-09": "unstated-uncertainty-or-competence-boundary",
}


@dataclass(frozen=True, slots=True)
class AssessmentDecision:
    weighted_score: float
    all_domains_at_least_70: bool
    critical_domains_at_least_80: bool
    unresolved_critical_failures: tuple[str, ...]
    decision: str


def score_assessment(
    domain_scores: dict[str, float], *, unresolved_critical_failures: tuple[str, ...] = ()
) -> AssessmentDecision:
    """Apply the eight-domain MU/FDE assessment gates without inventing evidence.

    This function evaluates supplied scores; it does not manufacture the scores. A caller
    must bind those values to independent evidence in the surrounding GymAct receipt path.
    """
    if set(domain_scores) != set(ASSESSMENT_DOMAINS):
        missing = sorted(set(ASSESSMENT_DOMAINS) - set(domain_scores))
        extra = sorted(set(domain_scores) - set(ASSESSMENT_DOMAINS))
        raise ValueError(f"assessment requires exactly D1-D8; missing={missing}, extra={extra}")
    for domain, score in domain_scores.items():
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(f"{domain} score must be numeric in [0,100]")
    unknown_cf = sorted(set(unresolved_critical_failures) - set(CRITICAL_FAILURES))
    if unknown_cf:
        raise ValueError(f"unknown critical failures: {unknown_cf}")
    weighted = sum(float(domain_scores[d]) for d in ASSESSMENT_DOMAINS) / len(ASSESSMENT_DOMAINS)
    all_70 = all(domain_scores[d] >= 70 for d in ASSESSMENT_DOMAINS)
    critical_80 = all(domain_scores[d] >= 80 for d in ("D4", "D5", "D6"))
    if unresolved_critical_failures:
        decision = "HOLD"
    elif all_70 and critical_80:
        decision = "CERTIFY"
    elif sum(score < 70 for score in domain_scores.values()) <= 2:
        decision = "TARGETED_REASSESSMENT"
    else:
        decision = "FULL_REASSESSMENT"
    return AssessmentDecision(
        weighted_score=round(weighted, 3),
        all_domains_at_least_70=all_70,
        critical_domains_at_least_80=critical_80,
        unresolved_critical_failures=tuple(unresolved_critical_failures),
        decision=decision,
    )
