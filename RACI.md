# Silicon Errata Lifecycle — RACI Matrix

**Version:** 1.0  
**Scope:** Errata from vendor publication through SOP gate sign-off

**Key:** R = Responsible · A = Accountable · C = Consulted · I = Informed

---

## Roles

| Role | Description |
|------|-------------|
| **Chip Vendor Team** | Receives vendor errata PDFs, owns initial data ingestion |
| **OEM SW Team** | Implements software workarounds, assesses impact per ECU |
| **Safety Team** | Reviews safety-critical errata, owns verification, issues safety evidence |
| **Release Gate Owner** | Signs off SOP; has final accountability for errata resolution status |

---

## RACI Table

| Activity | Chip Vendor Team | OEM SW Team | Safety Team | Release Gate Owner |
|----------|:----------------:|:-----------:|:-----------:|:-----------------:|
| **Monitor vendor errata publications** | R | I | I | I |
| **Ingest PDF into system (`POST /ingest/pdf`)** | R | C | I | I |
| **Initial triage: set severity, status → triaged** | C | R | C | I |
| **Assess ECU impact (link errata to ECUs)** | I | R | C | I |
| **Identify and implement SW workaround** | C | R | I | I |
| **Identify HW respin requirement** | R | C | A | I |
| **Set `safety_blocking` flag** | I | R | A | I |
| **Update status → mitigated** | I | R | C | I |
| **Independent safety verification** | I | C | R | I |
| **Update status → verified** | I | I | R | A |
| **Generate compliance report for SOP gate** | I | C | C | R |
| **Accept / reject SOP based on safety_blocking_open** | I | I | C | R |
| **Update status → closed post-SOP** | I | R | C | A |
| **Document errata in release notes** | I | R | C | A |

---

## Escalation Paths

| Trigger | Action | Escalates To |
|---------|--------|-------------|
| New critical errata discovered post-SOP | Emergency triage within 24h | Release Gate Owner |
| safety_blocking errata cannot be mitigated in software | Hardware respin evaluation | Program Director |
| Parse confidence < 0.7 on auto-ingested record | Manual field review required before triage | OEM SW Team lead |
| Vendor errata contradicts existing workaround | Re-verification required | Safety Team |

---

## SOP Gate Criteria

The **Release Gate Owner** will not sign SOP if any of the following are true:

1. `safety_blocking_open > 0` in the compliance report for any production chip
2. Any errata with `severity = critical` and `status = detected` or `triaged`
3. Any errata with `parsed_by_ai = true` that has not been manually reviewed

These metrics are available directly from `GET /report/{chip_id}`.
