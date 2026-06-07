# Silicon Errata Intelligence API — Product Requirements Document

**Version:** 1.0  
**Status:** Draft  
**Author:** Ishan Srivastava, MEM — NC State University  
**Audience:** OEM Software Teams, Safety Teams, Release Gate Owners

---

## 1. Problem Statement

Every semiconductor vendor — NXP, Renesas, Infineon, ARM — publishes errata documents: known bugs in shipped silicon, distributed as PDFs. An automotive OEM running the same chip in 50–100 ECUs needs to know at any point:

- Which errata affect which ECU?
- Which have software workarounds available, and have those been applied?
- Which require a hardware respin, and does that block the current program?
- Which are blocking safety certification (ISO 26262, IEC 61508)?

Today, this tracking is done manually — engineers reading PDFs and updating spreadsheets. This process is slow, error-prone, and produces no audit trail. The Silicon Errata Intelligence API automates the ingestion, tracking, and reporting of this data.

---

## 2. Goals

| Goal | Metric |
|------|--------|
| Eliminate manual PDF reading for errata tracking | PDF upload → structured records in < 30s |
| Provide queryable errata database across all chips and ECUs | `GET /errata/search` returns results in < 500ms |
| Produce a compliance summary engineers can use in safety reviews | `GET /report/{chip_id}` returns all required metrics |
| Flag safety-blocking errata automatically | `safety_blocking` field set via keyword heuristic on ingest |
| Provide an audit trail for all errata state changes | `status` lifecycle field with timestamps |

---

## 3. Errata Lifecycle

Each errata record moves through a defined set of states. Transitions are triggered by engineering teams and gated by the safety team before closing.

```
detected → triaged → mitigated → verified → closed
```

| State | Owner | Entry Criteria | Exit Criteria |
|-------|-------|----------------|---------------|
| **detected** | Auto-ingest / chip vendor | Vendor publishes errata document | Engineering team has reviewed and assessed |
| **triaged** | OEM SW Team | Errata reviewed | Impact assessed, mitigation path defined |
| **mitigated** | OEM SW Team | Mitigation path known | Software workaround or HW plan implemented and tested |
| **verified** | Safety Team | Mitigation implemented | Independent verification complete; safety evidence documented |
| **closed** | Release Gate Owner | Safety verification passed | No further action required; errata recorded in release docs |

### Safety-blocking errata
Errata flagged `safety_blocking=true` must reach **verified** status before a SOP (Start of Production) gate can be signed off. The compliance report (`GET /report/{chip_id}`) surfaces `safety_blocking_open` as the primary SOP gate metric.

---

## 4. Functional Requirements

### 4.1 Ingestion
- **FR-ING-01:** System shall accept PDF uploads and extract errata records via structured text parsing.
- **FR-ING-02:** System shall accept bulk JSON imports for pre-structured errata data.
- **FR-ING-03:** Every auto-parsed record shall be marked `parsed_by_ai=true` to indicate it requires human review.
- **FR-ING-04:** Parser shall assign a `parse_confidence` score (0.0–1.0) to each record.
- **FR-ING-05:** System shall skip duplicate errata (same `errata_id` + `chip_id`) and report them in the ingestion response.
- **FR-ING-06:** Safety-blocking flag shall be set automatically by keyword heuristic on ingest.

### 4.2 Querying
- **FR-QRY-01:** System shall support filtering by chip family, silicon revision, ECU name, severity, and status — individually and in combination.
- **FR-QRY-02:** Results shall be ordered by severity (critical first).
- **FR-QRY-03:** CLI query `--chip S32K344 --revision B --ecu BMS` shall return all errata affecting that ECU on that chip revision.

### 4.3 Lifecycle management
- **FR-LCM-01:** Any errata field (severity, status, mitigation_type, safety_blocking) shall be updatable via `PATCH /errata/{id}`.
- **FR-LCM-02:** Status transitions shall not be validated (any state → any state) to allow corrections.

### 4.4 Compliance reporting
- **FR-RPT-01:** `GET /report/{chip_id}` shall return total errata count, breakdown by severity and status, open critical count, safety-blocking counts, and mitigation coverage %.
- **FR-RPT-02:** Report shall be available in JSON and Markdown format.
- **FR-RPT-03:** CLI `report` subcommand shall render the report as a terminal table.

### 4.5 CLI
- **FR-CLI-01:** `query` subcommand shall wrap `GET /errata/search` with all filter flags.
- **FR-CLI-02:** `report` subcommand shall wrap `GET /report/{chip_id}` with `--format md` support.
- **FR-CLI-03:** `ingest` subcommand shall support `--pdf` and `--json` file upload.
- **FR-CLI-04:** `chips` subcommand shall list all chips with errata counts.

---

## 5. Non-functional Requirements

| Requirement | Target |
|-------------|--------|
| API response time (p95) | < 500ms for all query endpoints |
| PDF ingestion time | < 30s for a 50-page errata document |
| Test coverage | > 90% line coverage on all modules |
| Database | PostgreSQL in production; SQLite for local dev and CI |
| Deployment | Docker Compose (API + DB); single `docker-compose up` to start |

---

## 6. Out of Scope (v1.0)

- User authentication and access control
- Errata change notification / alerting
- Integration with chip vendor APIs (all ingestion is manual or PDF-based)
- Web UI (CLI + Swagger UI is the interface)
- Multi-tenant / multi-OEM support
