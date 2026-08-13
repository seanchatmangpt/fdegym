# fdegym

**Fortune-5 forward-deployed engineering gym built on DFCM, GymAct, and ggen.**

`fdegym` is not a cloud-certification flash-card set and it does not pretend a static list can contain every cloud feature. It models FDE work as a bounded executable graph:

```text
business mission
  × cloud provider topology
  × service
  × capability family
  × protocol
  × FDE role
  × lifecycle stage
  × failure mode
  × control domain
  × quality attribute
  → candidate architecture
  → GymAct admission / BRCE execution
  → verification / receipt / replay / handoff
```

## Why the graph is maximal without being fake

For AWS, Azure, and GCP, provider region/service identity is loaded from GymAct's provider-grounded `cloud_topology` module at runtime. `fdegym` does **not** copy or invent those catalogs. Cross-provider architecture dimensions are explicit and extensible: 40+ capability families, 60+ protocols/standards, FDE roles, lifecycle stages, failure modes, enterprise controls, and quality attributes.

The Cartesian product is never materialized. `PossibilitySpace` uses deterministic mixed-radix unranking, so an enormous DFCM graph can be paged, filtered, hashed, compared, and replayed with bounded memory.

## Fortune-5 scenario portfolio

The first pack includes global identity, regulated payments, media supply chain, enterprise GenAI, zero-downtime migration, ransomware recovery, multi-cloud sovereignty, API/event ecosystems, FinOps rearchitecture, and M&A platform integration. Every scenario carries required capability families, protocols, controls, failure injections, and evidence obligations.

The assessment rail implements eight equally weighted domains (D1-D8), the all-domains `>=70` gate, the stronger D4/D5/D6 `>=80` gate, and typed critical failures CF-01..CF-09. Supplied scores are evaluated but never inferred from reputation or self-report; the caller must bind them to independent evidence.

## GymAct boundary

`FDEProvider` satisfies GymAct's environment-provider contract. Its READ capabilities inspect the graph and grounded topology. Its DO capabilities only mutate the bounded training world: candidate selection, simulated deployment, control application, failure injection, recovery, and rollback. The environment sets `requires_authority=True`, so a production GymAct runtime can keep consequential action behind its authority/BRCE boundary.

**No live cloud mutation is implemented or implied here.** A real AWS/Azure/GCP adapter must be separately authorized, executed, independently verified, and represented by solved OCEL replay evidence before any live-cloud standing can be claimed.

Install GymAct in the same environment when exercising the integration:

```bash
pip install -e ../gymact
pip install -e .
fdegym topology --provider aws
fdegym probe --provider aws --scenario global-identity
```

Without GymAct, deterministic DFCM/scenario/catalog functions remain usable and runtime-specific commands return an explicit `UNSUPPORTED:GYMACT_RUNTIME_NOT_INSTALLED` boundary.

## ggen

`ggen/fde-gym-pack/ontology.ttl` is the semantic source for generated FDE profile projections. It uses public vocabularies (`PROV-O`, `SKOS`, `SOSA`, `DCTERMS`, `SHACL`) and keeps `urn:fdegym:*` to profile/ABox identities and shapes rather than inventing a parallel enterprise ontology.

```bash
ggen sync run
```

The pack is intentionally separate from Python runtime logic: ggen manufactures semantic/static projections; GymAct owns runtime execution and receipts.

## Local verification

```bash
python -m pip install -e .
pytest
ruff check src tests
fdegym catalog
fdegym scenarios
```

A green deterministic-core test suite proves only the pure FDE graph/world implementation exercised by those tests. It is **not** evidence that a real cloud episode was executed. Runtime standing remains bounded by GymAct's own receipts and replay rules.
