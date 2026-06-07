"""
Milestone 1 — Model tests.

Covers: table creation, CRUD operations, relationships,
enum validation, cascade deletes, and constraint checks.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.chip import Chip
from app.models.errata import Errata, SeverityEnum, MitigationTypeEnum, StatusEnum
from app.models.workaround import Workaround
from app.models.ecu_errata import EcuErrata


# ------------------------------------------------------------------ #
# Chip model                                                            #
# ------------------------------------------------------------------ #

class TestChipModel:

    def test_create_chip(self, db):
        chip = Chip(vendor="NXP", family="S32K344", revision="B")
        db.add(chip)
        db.commit()
        assert chip.id is not None
        assert chip.vendor == "NXP"
        assert chip.family == "S32K344"
        assert chip.revision == "B"

    def test_chip_created_at_auto_set(self, db):
        chip = Chip(vendor="NXP", family="S32K344", revision="B")
        db.add(chip)
        db.commit()
        assert chip.created_at is not None

    def test_chip_optional_fields_nullable(self, db):
        chip = Chip(vendor="Renesas", family="RH850/U2A", revision="1.1")
        db.add(chip)
        db.commit()
        assert chip.description is None
        assert chip.datasheet_url is None

    def test_chip_repr(self, db):
        chip = Chip(vendor="ARM", family="Cortex-M33", revision="r0p4")
        db.add(chip)
        db.commit()
        assert "ARM" in repr(chip)
        assert "Cortex-M33" in repr(chip)

    def test_multiple_chips(self, db):
        chips = [
            Chip(vendor="NXP", family="S32K344", revision="B"),
            Chip(vendor="Renesas", family="RH850/U2A", revision="1.1"),
            Chip(vendor="Infineon", family="TC397", revision="AB"),
        ]
        db.add_all(chips)
        db.commit()
        result = db.query(Chip).all()
        assert len(result) == 3

    def test_chip_vendor_required(self, db):
        chip = Chip(family="S32K344", revision="B")  # vendor missing
        db.add(chip)
        with pytest.raises(Exception):
            db.commit()

    def test_query_chip_by_vendor(self, db):
        db.add_all([
            Chip(vendor="NXP", family="S32K344", revision="B"),
            Chip(vendor="NXP", family="S32K148", revision="A"),
            Chip(vendor="Renesas", family="RH850/U2A", revision="1.1"),
        ])
        db.commit()
        nxp_chips = db.query(Chip).filter(Chip.vendor == "NXP").all()
        assert len(nxp_chips) == 2


# ------------------------------------------------------------------ #
# Errata model                                                          #
# ------------------------------------------------------------------ #

class TestErrataModel:

    def test_create_errata(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id,
            errata_id="ERR-001",
            title="CAN FD frame corruption",
            description="Frame corrupted under high load.",
            severity=SeverityEnum.critical,
            mitigation_type=MitigationTypeEnum.software,
            status=StatusEnum.mitigated,
            safety_blocking=True,
        )
        db.add(errata)
        db.commit()
        assert errata.id is not None
        assert errata.severity == SeverityEnum.critical
        assert errata.safety_blocking is True

    def test_errata_default_status_is_detected(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id,
            errata_id="ERR-002",
            title="Test errata",
            description="Description.",
            severity=SeverityEnum.low,
            mitigation_type=MitigationTypeEnum.none,
        )
        db.add(errata)
        db.commit()
        assert errata.status == StatusEnum.detected

    def test_errata_default_safety_blocking_false(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id,
            errata_id="ERR-003",
            title="Minor errata",
            description="Description.",
            severity=SeverityEnum.low,
            mitigation_type=MitigationTypeEnum.none,
        )
        db.add(errata)
        db.commit()
        assert errata.safety_blocking is False

    def test_errata_all_severity_values(self, db, sample_chip):
        for i, sev in enumerate(SeverityEnum):
            errata = Errata(
                chip_id=sample_chip.id,
                errata_id=f"ERR-SEV-{i}",
                title=f"Severity test {sev}",
                description=".",
                severity=sev,
                mitigation_type=MitigationTypeEnum.none,
                status=StatusEnum.detected,
            )
            db.add(errata)
        db.commit()
        count = db.query(Errata).filter(Errata.chip_id == sample_chip.id).count()
        assert count == len(list(SeverityEnum))

    def test_errata_all_status_values(self, db, sample_chip):
        for i, status in enumerate(StatusEnum):
            errata = Errata(
                chip_id=sample_chip.id,
                errata_id=f"ERR-STA-{i}",
                title=f"Status test {status}",
                description=".",
                severity=SeverityEnum.low,
                mitigation_type=MitigationTypeEnum.none,
                status=status,
            )
            db.add(errata)
        db.commit()
        results = db.query(Errata).filter(Errata.chip_id == sample_chip.id).all()
        statuses = {e.status for e in results}
        assert statuses == set(StatusEnum)

    def test_errata_chip_relationship(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id,
            errata_id="ERR-REL-001",
            title="Relationship test",
            description=".",
            severity=SeverityEnum.medium,
            mitigation_type=MitigationTypeEnum.software,
        )
        db.add(errata)
        db.commit()
        db.refresh(errata)
        assert errata.chip.vendor == "NXP"
        assert errata.chip.family == "S32K344"

    def test_chip_errata_backref(self, db, sample_chip):
        errata1 = Errata(chip_id=sample_chip.id, errata_id="E1", title="Bug 1",
                         description=".", severity=SeverityEnum.low,
                         mitigation_type=MitigationTypeEnum.none)
        errata2 = Errata(chip_id=sample_chip.id, errata_id="E2", title="Bug 2",
                         description=".", severity=SeverityEnum.high,
                         mitigation_type=MitigationTypeEnum.software)
        db.add_all([errata1, errata2])
        db.commit()
        db.refresh(sample_chip)
        assert len(sample_chip.errata) == 2

    def test_filter_by_severity_and_status(self, db, sample_chip):
        db.add_all([
            Errata(chip_id=sample_chip.id, errata_id="F1", title="t",
                   description=".", severity=SeverityEnum.critical,
                   mitigation_type=MitigationTypeEnum.software,
                   status=StatusEnum.open if hasattr(StatusEnum, 'open') else StatusEnum.detected),
            Errata(chip_id=sample_chip.id, errata_id="F2", title="t",
                   description=".", severity=SeverityEnum.low,
                   mitigation_type=MitigationTypeEnum.none,
                   status=StatusEnum.closed),
        ])
        db.commit()
        critical = (db.query(Errata)
                    .filter(Errata.chip_id == sample_chip.id,
                            Errata.severity == SeverityEnum.critical)
                    .all())
        assert len(critical) == 1
        assert critical[0].errata_id == "F1"

    def test_safety_blocking_filter(self, db, sample_chip):
        db.add_all([
            Errata(chip_id=sample_chip.id, errata_id="S1", title="t",
                   description=".", severity=SeverityEnum.critical,
                   mitigation_type=MitigationTypeEnum.software,
                   safety_blocking=True),
            Errata(chip_id=sample_chip.id, errata_id="S2", title="t",
                   description=".", severity=SeverityEnum.low,
                   mitigation_type=MitigationTypeEnum.none,
                   safety_blocking=False),
        ])
        db.commit()
        blocking = (db.query(Errata)
                    .filter(Errata.safety_blocking.is_(True))
                    .all())
        assert len(blocking) == 1
        assert blocking[0].errata_id == "S1"

    def test_errata_repr(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id, errata_id="ERR-REPR",
            title="Repr test", description=".",
            severity=SeverityEnum.high,
            mitigation_type=MitigationTypeEnum.hardware,
        )
        db.add(errata)
        db.commit()
        r = repr(errata)
        assert "ERR-REPR" in r
        assert "high" in r


# ------------------------------------------------------------------ #
# Workaround model                                                      #
# ------------------------------------------------------------------ #

class TestWorkaroundModel:

    def test_create_workaround(self, db, sample_errata):
        w = Workaround(
            errata_id=sample_errata.id,
            description="Disable ISO mode",
            code_snippet="CAN0->CTRL2 &= ~CAN_CTRL2_ISOCANFDEN_MASK;",
            author="NXP AppEng",
        )
        db.add(w)
        db.commit()
        assert w.id is not None
        assert w.errata_id == sample_errata.id

    def test_workaround_code_snippet_optional(self, db, sample_errata):
        w = Workaround(
            errata_id=sample_errata.id,
            description="Hardware respin required. No software workaround.",
        )
        db.add(w)
        db.commit()
        assert w.code_snippet is None
        assert w.author is None

    def test_workaround_errata_relationship(self, db, sample_errata):
        w = Workaround(
            errata_id=sample_errata.id,
            description="Fix description",
        )
        db.add(w)
        db.commit()
        db.refresh(w)
        assert w.errata.errata_id == "ERR_TEST-001"

    def test_multiple_workarounds_per_errata(self, db, sample_errata):
        db.add_all([
            Workaround(errata_id=sample_errata.id, description="Quick SW fix"),
            Workaround(errata_id=sample_errata.id, description="Full HW respin plan"),
        ])
        db.commit()
        db.refresh(sample_errata)
        assert len(sample_errata.workarounds) == 2

    def test_cascade_delete_workarounds(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id, errata_id="CASCADE-001",
            title="Will be deleted", description=".",
            severity=SeverityEnum.low,
            mitigation_type=MitigationTypeEnum.none,
        )
        db.add(errata)
        db.commit()
        w = Workaround(errata_id=errata.id, description="Workaround")
        db.add(w)
        db.commit()
        workaround_id = w.id

        db.delete(errata)
        db.commit()

        deleted = db.query(Workaround).filter(Workaround.id == workaround_id).first()
        assert deleted is None


# ------------------------------------------------------------------ #
# EcuErrata model                                                       #
# ------------------------------------------------------------------ #

class TestEcuErrataModel:

    def test_create_ecu_errata(self, db, sample_errata):
        link = EcuErrata(
            errata_id=sample_errata.id,
            ecu_name="BMS_ECU",
            ecu_project="EV Platform Gen2",
            notes="Workaround applied in CAN driver v2.3.1.",
        )
        db.add(link)
        db.commit()
        assert link.id is not None
        assert link.ecu_name == "BMS_ECU"

    def test_same_errata_multiple_ecus(self, db, sample_errata):
        db.add_all([
            EcuErrata(errata_id=sample_errata.id, ecu_name="BMS_ECU"),
            EcuErrata(errata_id=sample_errata.id, ecu_name="Gateway_ECU"),
            EcuErrata(errata_id=sample_errata.id, ecu_name="ADAS_ECU"),
        ])
        db.commit()
        db.refresh(sample_errata)
        assert len(sample_errata.ecu_links) == 3

    def test_ecu_errata_optional_fields(self, db, sample_errata):
        link = EcuErrata(errata_id=sample_errata.id, ecu_name="Minimal_ECU")
        db.add(link)
        db.commit()
        assert link.ecu_project is None
        assert link.notes is None

    def test_cascade_delete_ecu_links(self, db, sample_chip):
        errata = Errata(
            chip_id=sample_chip.id, errata_id="CASCADE-ECU-001",
            title="ECU cascade test", description=".",
            severity=SeverityEnum.medium,
            mitigation_type=MitigationTypeEnum.software,
        )
        db.add(errata)
        db.commit()
        link = EcuErrata(errata_id=errata.id, ecu_name="Test_ECU")
        db.add(link)
        db.commit()
        link_id = link.id

        db.delete(errata)
        db.commit()

        deleted = db.query(EcuErrata).filter(EcuErrata.id == link_id).first()
        assert deleted is None

    def test_filter_errata_by_ecu_name(self, db, sample_chip):
        e1 = Errata(chip_id=sample_chip.id, errata_id="ECU-F1", title="t",
                    description=".", severity=SeverityEnum.critical,
                    mitigation_type=MitigationTypeEnum.software)
        e2 = Errata(chip_id=sample_chip.id, errata_id="ECU-F2", title="t",
                    description=".", severity=SeverityEnum.low,
                    mitigation_type=MitigationTypeEnum.none)
        db.add_all([e1, e2])
        db.commit()

        db.add_all([
            EcuErrata(errata_id=e1.id, ecu_name="BMS_ECU"),
            EcuErrata(errata_id=e2.id, ecu_name="Gateway_ECU"),
        ])
        db.commit()

        bms_errata = (
            db.query(Errata)
            .join(EcuErrata, EcuErrata.errata_id == Errata.id)
            .filter(EcuErrata.ecu_name == "BMS_ECU")
            .all()
        )
        assert len(bms_errata) == 1
        assert bms_errata[0].errata_id == "ECU-F1"


# ------------------------------------------------------------------ #
# Cross-model / integration queries                                     #
# ------------------------------------------------------------------ #

class TestCrossModelQueries:

    def test_full_chain_chip_errata_workaround_ecu(self, db):
        """End-to-end: create a chip → errata → workaround + ECU link, then read back."""
        chip = Chip(vendor="Renesas", family="RH850/U2A", revision="1.1")
        db.add(chip)
        db.commit()

        errata = Errata(
            chip_id=chip.id,
            errata_id="ERR_RH850-002",
            title="Watchdog stall under interrupt load",
            description="WDTA counter stalls when OSTM is delayed > 3 cycles.",
            severity=SeverityEnum.critical,
            mitigation_type=MitigationTypeEnum.hardware,
            status=StatusEnum.detected,
            safety_blocking=True,
        )
        db.add(errata)
        db.commit()

        w = Workaround(errata_id=errata.id,
                       description="Hardware respin to Rev 1.2 required.")
        ecu_link = EcuErrata(errata_id=errata.id, ecu_name="ADAS_ECU",
                             ecu_project="ADAS Platform V3",
                             notes="Blocking tape-out.")
        db.add_all([w, ecu_link])
        db.commit()

        # Read back via chip relationship
        db.refresh(chip)
        assert len(chip.errata) == 1
        read_errata = chip.errata[0]
        assert read_errata.safety_blocking is True
        assert len(read_errata.workarounds) == 1
        assert len(read_errata.ecu_links) == 1
        assert read_errata.ecu_links[0].ecu_name == "ADAS_ECU"

    def test_count_open_critical_safety_blocking(self, db, sample_chip):
        """Query pattern used by the compliance report endpoint."""
        errata_data = [
            ("E1", SeverityEnum.critical, StatusEnum.detected, True),
            ("E2", SeverityEnum.critical, StatusEnum.mitigated, True),
            ("E3", SeverityEnum.high,     StatusEnum.detected, True),
            ("E4", SeverityEnum.low,      StatusEnum.detected, False),
        ]
        for eid, sev, sta, sb in errata_data:
            db.add(Errata(
                chip_id=sample_chip.id, errata_id=eid,
                title="t", description=".",
                severity=sev, mitigation_type=MitigationTypeEnum.software,
                status=sta, safety_blocking=sb,
            ))
        db.commit()

        open_critical = (
            db.query(Errata)
            .filter(
                Errata.chip_id == sample_chip.id,
                Errata.severity == SeverityEnum.critical,
                Errata.status == StatusEnum.detected,
            )
            .count()
        )
        assert open_critical == 1  # only E1 is critical + detected

        safety_blocking_total = (
            db.query(Errata)
            .filter(
                Errata.chip_id == sample_chip.id,
                Errata.safety_blocking.is_(True),
            )
            .count()
        )
        assert safety_blocking_total == 3

    def test_enum_string_values_stored_correctly(self, db, sample_chip):
        """Confirm enum values stored as their string representation."""
        errata = Errata(
            chip_id=sample_chip.id,
            errata_id="ENUM-TEST",
            title="Enum test",
            description=".",
            severity=SeverityEnum.high,
            mitigation_type=MitigationTypeEnum.software,
            status=StatusEnum.triaged,
        )
        db.add(errata)
        db.commit()

        # Query the raw stored value directly
        result = db.query(Errata).filter(Errata.errata_id == "ENUM-TEST").one()
        assert result.severity == "high"
        assert result.mitigation_type == "software"
        assert result.status == "triaged"
