# Silicon Errata — Risk Register

**Version:** 1.0  
**Scope:** Risks arising when errata are discovered or change state post-SOP  
**Review Cadence:** Quarterly or upon any new critical errata discovery

**Likelihood:** 1 (rare) → 5 (near-certain)  
**Impact:** 1 (negligible) → 5 (program-stopping)  
**Risk Score = Likelihood × Impact**

---

## Risk Register

| ID | Risk | Likelihood | Impact | Score | Owner | Mitigation | Contingency |
|----|------|:----------:|:------:|:-----:|-------|------------|-------------|
| **R-01** | Critical errata discovered after SOP with no software workaround | 2 | 5 | 10 | Release Gate Owner | Mandatory pre-SOP compliance report check; all critical errata must reach `verified` before gate | Emergency field stop; hardware respin assessment within 5 business days |
| **R-02** | Vendor publishes new errata revision that invalidates existing workaround | 3 | 4 | 12 | Chip Vendor Team | Weekly vendor bulletin monitoring; re-ingest on each new vendor document version | Re-triage affected errata; safety team re-verification before next delivery |
| **R-03** | Auto-parsed errata record has low confidence and incorrect severity | 4 | 3 | 12 | OEM SW Team | All `parsed_by_ai=true` records flagged in compliance report; mandatory manual review before triage | Reject any record for triage if `parse_confidence < 0.7` without manual correction |
| **R-04** | safety_blocking errata missed during triage (flag not set) | 2 | 5 | 10 | Safety Team | Safety keyword heuristic auto-sets flag on ingest; safety team reviews all high/critical errata | Retrospective safety review; re-verification if flag was missed before SOP |
| **R-05** | Chip vendor discontinues or changes errata PDF format | 3 | 2 | 6 | Chip Vendor Team | Parser uses flexible field matching; fall back to JSON bulk import | Update parser patterns for new format; JSON import available as immediate workaround |
| **R-06** | Errata affects multiple chip revisions but only one revision is tracked | 3 | 3 | 9 | OEM SW Team | `affected_silicon_revisions` field captured on ingest; query by revision supported | Audit all ECUs for affected revision; update errata record with full revision list |
| **R-07** | OEM runs same chip in multiple ECUs but only tracks one ECU link | 3 | 4 | 12 | OEM SW Team | ECU linking is many-to-many; checklist item at triage to link all affected ECUs | Cross-ECU audit query: `GET /errata/search?chip=X&severity=critical` |
| **R-08** | Database contains stale open errata that are actually resolved in production | 2 | 2 | 4 | OEM SW Team | Quarterly sweep of all `status=mitigated` errata older than 90 days; prompt for verification | Bulk status update via `PATCH /errata/{id}` to advance lifecycle |
| **R-09** | CLI / API connection lost during a SOP gate review | 2 | 3 | 6 | Release Gate Owner | Export compliance report to Markdown before gate meeting; keep offline copy | Use `GET /report/{chip_id}?format=md` to export ahead of meeting |
| **R-10** | Errata PDF contains ambiguous or vendor-specific terminology not in normalization map | 4 | 1 | 4 | OEM SW Team | Parse warnings surfaced in ingestion response; low confidence triggers review | Manual correction via `PATCH /errata/{id}`; add new alias to normalization map |

---

## Risk Heatmap

```
Impact
  5  |        | R-01   | R-04   |        |
  4  |        | R-07   | R-02   |        |
  3  |        | R-06   | R-09   | R-03   |
  2  |        | R-08   | R-05   | R-10   |
  1  |        |        |        |        |
     +--------+--------+--------+--------+
     Rare(1)  Low(2)   Med(3)   High(4)   Likely(5)
                      Likelihood
```

**High-priority (score ≥ 10):** R-01, R-02, R-03, R-04, R-07  
**Medium-priority (score 5–9):** R-05, R-06, R-09  
**Low-priority (score < 5):** R-08, R-10

---

## Review Log

| Date | Reviewer | Changes |
|------|----------|---------|
| 2026-06-01 | Ishan Srivastava | Initial version |
