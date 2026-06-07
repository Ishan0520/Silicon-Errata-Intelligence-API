<div align="center">

# Silicon Errata Intelligence API

**Automated silicon errata tracking for automotive OEM teams**

[![CI](https://github.com/yourusername/silicon-errata-api/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/silicon-errata-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-382%20passed-brightgreen?logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)


</div>

---

## The Problem

Every semiconductor company — NXP, Renesas, Infineon, ARM — publishes **errata documents**: known bugs in shipped silicon, released as PDFs. An automotive OEM using NXP S32K344 or Renesas RH850 across 100 different ECUs needs to know:

- Which errata affect which ECU?
- Which have software workarounds — and have those been applied?
- Which require a hardware respin?
- Which are **blocking safety certification** (ISO 26262)?

This API automates the entire pipeline — from PDF ingestion to SOP gate compliance reporting.

---

## What It Does

```
Vendor PDF  ──▶  Parser  ──▶  PostgreSQL  ──▶  REST API  ──▶  CLI / Report
(NXP, Renesas)   (auto)       (structured)     (search,        (engineer
                               records)          filter)         queries)
```

| Capability | How |
|------------|-----|
| 📄 **Auto-ingest vendor PDFs** | Upload → structured records in seconds |
| 🔍 **Query by chip + ECU** | `GET /errata/search?chip=S32K344&revision=B&ecu=BMS` |
| 📊 **SOP compliance report** | Coverage %, open critical count, safety-blocking status |
| 🖥️ **Engineer CLI** | `python errata_cli.py query --chip S32K344 --ecu BMS` |
| 🔒 **Safety lifecycle tracking** | detected → triaged → mitigated → verified → closed |

---

## Quick Start

### Option A — Docker (one command)

```bash
git clone https://github.com/yourusername/silicon-errata-api
cd silicon-errata-api
docker-compose up -d
```

API live at **http://localhost:8000** · Interactive docs at **http://localhost:8000/docs**

Load sample data (NXP S32K344 + Renesas RH850):
```bash
docker-compose exec api python scripts/seed.py
```

### Option B — Local (no Docker needed)

```bash
# 1. Virtual environment
python3 -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows (cmd)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests — 382 tests, ~7 seconds
pytest tests/ -v

# 4. Start dev server (SQLite, no Postgres needed)
DATABASE_URL=sqlite:///./errata_dev.db uvicorn app.main:app --reload

# 5. Load sample data
DATABASE_URL=sqlite:///./errata_dev.db python scripts/seed.py
```

---

## CLI Usage

The CLI is the primary engineer interface — a thin wrapper around the REST API.

```bash
pip install requests
export ERRATA_API_URL=http://localhost:8000
```

### Query — the core workflow

```bash
# "Which errata affect the NXP S32K344 Rev B BMS ECU?"
python errata_cli.py query --chip S32K344 --revision B --ecu BMS
```

```
Found 2 errata:
────────────────────────────────────────────────────────────

  🔴 [ERR_S32K3-001] CAN FD: Frame corruption under high bus load 🚨 SAFETY
     Severity: CRITICAL  Status: 🔧 mitigated
     Mitigation: software

  🟠 [ERR_S32K3-003] Flash: ECC silent error after partial write 🚨 SAFETY
     Severity: HIGH      Status: 📋 triaged
     Mitigation: software
```

```bash
# Filter by severity and status
python errata_cli.py query --chip RH850 --severity critical --status detected

# Verbose mode shows descriptions + ECU links
python errata_cli.py query --chip S32K344 -v
```

### Compliance report

```bash
# Terminal dashboard
python errata_cli.py report --chip-id 1
```

```
════════════════════════════════════════════════════════════
  Compliance Report: NXP S32K344 Rev B
════════════════════════════════════════════════════════════

  ⚠ 1 open critical errata. 2 safety-blocking errata unresolved.
    Mitigation coverage: 66.7%.

  Metric                              Value
  ─────────────────────────────────────────────────────────
  Total errata                        3
  Open critical                       1
  Safety-blocking (total / open)      2 / 2
  Mitigation coverage                 66.7%
  Needs review (AI-parsed)            0

  Severity breakdown:
    🔴 Critical     1  █
    🟠 High         1  █
    🟡 Medium       1  █
    🟢 Low          0
```

```bash
# Export Markdown for safety review documents
python errata_cli.py report --chip-id 1 --format md > sop_report.md
```

### Ingest a vendor PDF

```bash
python errata_cli.py ingest --chip-id 1 --pdf ./nxp_s32k344_errata_rev3.pdf
```

```
Ingesting PDF: ./nxp_s32k344_errata_rev3.pdf
────────────────────────────────────────────
  Chip:    S32K344 (id=1)
  Parsed:  3
  Stored:  3
  Skipped: 0 (duplicates)

  Records:
    🔴 ERR_S32K3-001         ✓ stored
    🟠 ERR_S32K3-003         ✓ stored
    🟡 ERR_S32K3-002         ✓ stored
```

### All commands

```bash
python errata_cli.py query   --chip <name> --revision <rev> --ecu <name> [--severity] [--status] [-v]
python errata_cli.py report  --chip-id <id> [--format md]
python errata_cli.py ingest  --chip-id <id> --pdf <file> | --json <file>
python errata_cli.py chips   [--vendor <name>]
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/chips` | List all chips · filter `?vendor=NXP` |
| `GET` | `/chips/{id}/errata` | Errata for a chip · filter `?severity=critical&status=detected&safety_blocking=true` |
| `POST` | `/errata` | Create errata record manually |
| `GET` | `/errata/{id}` | Get single errata record |
| `PATCH` | `/errata/{id}` | Update status, severity, safety_blocking |
| `GET` | `/errata/search` | Search across all chips · `?chip=S32K344&revision=B&ecu=BMS` |
| `POST` | `/ingest/pdf?chip_id=1` | Upload vendor PDF → auto-extracted records |
| `POST` | `/ingest/json` | Bulk import structured JSON |
| `GET` | `/report/{chip_id}` | Compliance summary · `?format=md` for Markdown |
| `GET` | `/health` | Liveness probe |
| `GET` | `/docs` | Interactive Swagger UI |

### Errata lifecycle

Every errata record moves through a defined lifecycle, tracked via `PATCH /errata/{id}`:

```
detected ──▶ triaged ──▶ mitigated ──▶ verified ──▶ closed
   │                                       │
   └── safety_blocking=true means ─────────┘
       must reach VERIFIED before SOP gate
```

### Compliance report fields

| Field | What it tells you |
|-------|-------------------|
| `total_errata` | Total bug count for this chip |
| `open_critical_count` | Critical bugs not yet verified or closed |
| `safety_blocking_total` | Bugs requiring safety sign-off |
| `safety_blocking_open` | Safety-blocking bugs still unresolved — **SOP gate metric** |
| `mitigation_coverage_pct` | % of bugs at mitigated / verified / closed |
| `needs_review_count` | Auto-parsed records needing human confirmation |

> **SOP rule:** Do not sign Start of Production if `safety_blocking_open > 0`.

---

## PDF Ingestion Format

The parser extracts structured fields from vendor errata PDFs (NXP, Renesas format):

```
Errata ID: ERR-001
Title: CAN FD: Frame corruption under high bus load
Severity: Critical
Mitigation Type: Software
Affected Revisions: B
Description: Under sustained high bus load (>70%) with CAN FD ISO mode
enabled, the FlexCAN peripheral may corrupt the last byte of a data frame.
Workaround: Disable ISO mode by setting CTRL2[ISOCANFDEN]=0.
```

Every auto-parsed record receives a **confidence score** (0.0–1.0):
- `1.0` — all fields cleanly extracted
- `< 1.0` — some fields defaulted (flagged in the ingest response with warnings)
- Records are marked `parsed_by_ai=true` until manually verified

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  Consumers                                                    │
│   errata_cli.py (query / report / ingest / chips)            │
│   Swagger UI at /docs                                         │
└───────────────────────────┬───────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼───────────────────────────────────┐
│  FastAPI application                                          │
│                                                               │
│   GET /chips              GET /errata/search                  │
│   GET /chips/{id}/errata  POST /errata  PATCH /errata/{id}   │
│   POST /ingest/pdf        POST /ingest/json                   │
│   GET /report/{chip_id}   GET /health                        │
│                                                               │
│   app/parser.py  ·  app/crud.py  ·  app/schemas.py           │
└───────────────────────────┬───────────────────────────────────┘
                            │ SQLAlchemy ORM
┌───────────────────────────▼───────────────────────────────────┐
│  Database                                                     │
│   PostgreSQL 16 (production via Docker)                       │
│   SQLite (local dev and CI — no setup needed)                │
│                                                               │
│   chips  ──▶  errata  ──▶  workarounds                       │
│                    └──▶  ecu_errata                           │
└───────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
silicon-errata-api/
│
├── app/                          # Application source
│   ├── main.py                   # FastAPI app + router wiring
│   ├── parser.py                 # PDF and JSON errata parser
│   ├── crud.py                   # All database operations
│   ├── schemas.py                # Pydantic request/response models
│   ├── db/
│   │   └── database.py           # SQLAlchemy engine + session
│   ├── models/                   # ORM models
│   │   ├── chip.py               # Chip family + revision
│   │   ├── errata.py             # Errata record + enums
│   │   ├── workaround.py         # Mitigation steps + code snippets
│   │   └── ecu_errata.py         # ECU ↔ errata join table
│   └── routers/                  # Endpoint handlers
│       ├── chips.py              # GET /chips, GET /chips/{id}/errata
│       ├── errata.py             # POST/GET/PATCH /errata, GET /errata/search
│       ├── ingest.py             # POST /ingest/pdf, POST /ingest/json
│       └── report.py             # GET /report/{chip_id}
│
├── tests/                        # 382 tests, ~7 seconds
│   ├── conftest.py               # SQLite in-memory fixtures (StaticPool)
│   ├── fixtures/make_pdf.py      # Generates test PDFs with reportlab
│   ├── test_models.py            # ORM + cascade delete tests (42)
│   ├── test_seed.py              # Seed data integrity tests (12)
│   ├── test_parser.py            # Parser unit tests — PDF + JSON (48)
│   ├── test_api_chips.py         # /chips endpoint tests (21)
│   ├── test_api_errata.py        # /errata endpoint tests (39)
│   ├── test_api_ingest.py        # /ingest endpoint tests (45)
│   ├── test_api_report.py        # /report endpoint tests (27)
│   ├── test_cli.py               # CLI argument + handler tests (42)
│   └── test_milestone5.py        # Dockerfile, CI, README validation (106)
│
├── scripts/
│   └── seed.py                   # Sample data: NXP S32K344 + Renesas RH850
│
├── docs/                         # TPM artifacts
│   ├── PRD.md                    # Product Requirements Document
│   ├── RACI.md                   # Responsibility matrix
│   └── RISK_REGISTER.md          # Risk register (10 risks)
│
├── alembic/                      # Database migrations
│   ├── env.py
│   └── versions/
│
├── errata_cli.py                 # CLI tool (query / report / ingest / chips)
├── Dockerfile                    # Multi-stage build, non-root user
├── docker-compose.yml            # API + PostgreSQL services
├── requirements.txt
├── alembic.ini
├── pytest.ini
└── .github/
    └── workflows/
        └── ci.yml                # Test → Docker build → smoke test
```

---

## Testing

```bash
# Full suite
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov=errata_cli --cov-report=term-missing

# Single module
pytest tests/test_parser.py -v
pytest tests/test_api_report.py -v
```

**382 tests across 9 test files.** All tests run against an in-memory SQLite database — no Docker, no Postgres needed.

| Test file | What it covers | Count |
|-----------|---------------|-------|
| `test_models.py` | ORM models, relationships, cascade deletes | 42 |
| `test_seed.py` | Seed data integrity | 12 |
| `test_parser.py` | PDF + JSON parser, confidence scoring, normalization | 48 |
| `test_api_chips.py` | `/chips` endpoints, filters | 21 |
| `test_api_errata.py` | `/errata` CRUD, search, lifecycle | 39 |
| `test_api_ingest.py` | PDF/JSON ingestion, duplicates, degraded data | 45 |
| `test_api_report.py` | Compliance metrics, Markdown export | 27 |
| `test_cli.py` | Argument parser, command handlers, formatters | 42 |
| `test_milestone5.py` | Dockerfile, docker-compose, CI YAML, README | 106 |

---

## CI/CD

GitHub Actions runs on every push and pull request to `main`:

```
push / PR
    │
    ├── test          Run 382 pytest tests · coverage ≥ 80% required
    │
    ├── docker-build  Build multi-stage image · smoke test /health /chips /docs
    │   (needs: test)
    │
    └── lint          Validate docker-compose.yml · alembic.ini · required files
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./errata_dev.db` | Database connection (PostgreSQL in production) |
| `ERRATA_API_URL` | `http://localhost:8000` | Used by the CLI tool |

---

## TPM Artifacts

This project includes three TPM documents in `/docs/` that demonstrate program management thinking alongside the working code:

| Document | Contents |
|----------|----------|
| [`docs/PRD.md`](docs/PRD.md) | Problem statement · errata lifecycle states with entry/exit criteria · functional requirements |
| [`docs/RACI.md`](docs/RACI.md) | Responsibility matrix across Chip Vendor / OEM SW / Safety / Release Gate Owner · SOP gate criteria |
| [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md) | 10 risks with likelihood/impact scoring · post-SOP discovery scenarios · AI-parse failure modes |

**The SOP gate rule** (from `RACI.md`, enforced by `GET /report/{chip_id}`):
> Do not sign Start of Production if `safety_blocking_open > 0` for any production chip.

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **FastAPI** | 0.115 | REST API framework · auto-generates Swagger UI |
| **SQLAlchemy** | 2.0 | ORM and query layer |
| **Alembic** | 1.13 | Database schema migrations |
| **pdfplumber** | 0.11 | PDF text extraction for errata ingestion |
| **PostgreSQL** | 16 | Production database (via Docker) |
| **SQLite** | built-in | Local dev + all CI tests |
| **pytest** | 8.3 | Test framework · 382 tests |
| **Docker + Compose** | - | Containerised deployment |
| **GitHub Actions** | - | CI pipeline: test → build → smoke test |

---

## Worked Example — Full Workflow

```bash
# 1. See what chips are registered
python errata_cli.py chips
#   ID  Vendor       Family               Rev        Errata
#    1  NXP          S32K344              B               3
#    2  Renesas      RH850/U2A            1.1             2

# 2. Ingest the latest vendor errata PDF
python errata_cli.py ingest --chip-id 1 --pdf ./nxp_s32k344_errata.pdf

# 3. Ask the engineer's question
python errata_cli.py query --chip S32K344 --revision B --ecu BMS

# 4. Advance status after safety team sign-off
curl -X PATCH http://localhost:8000/errata/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "verified"}'

# 5. Check SOP gate readiness
python errata_cli.py report --chip-id 1
# → safety_blocking_open: 1  ← cannot sign SOP yet

# 6. Export for safety review package
python errata_cli.py report --chip-id 1 --format md > docs/sop_errata_report.md
```

<div align="center">

</div>
