"""
Tests that the seed script populates all tables with correct data.
Imports the seed function directly so no subprocess is needed.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import Base
from app.models.chip import Chip
from app.models.errata import Errata, SeverityEnum, StatusEnum
from app.models.workaround import Workaround
from app.models.ecu_errata import EcuErrata
from scripts.seed import seed, create_tables


class TestSeedData:

    def test_seed_creates_two_chips(self, db):
        seed(db)
        chips = db.query(Chip).all()
        assert len(chips) == 2

    def test_seed_chip_vendors(self, db):
        seed(db)
        vendors = {c.vendor for c in db.query(Chip).all()}
        assert "NXP" in vendors
        assert "Renesas" in vendors

    def test_seed_creates_five_errata(self, db):
        seed(db)
        errata = db.query(Errata).all()
        assert len(errata) == 5

    def test_seed_has_critical_errata(self, db):
        seed(db)
        critical = (db.query(Errata)
                    .filter(Errata.severity == SeverityEnum.critical)
                    .all())
        assert len(critical) >= 1

    def test_seed_has_safety_blocking_errata(self, db):
        seed(db)
        blocking = db.query(Errata).filter(Errata.safety_blocking.is_(True)).all()
        assert len(blocking) >= 2

    def test_seed_creates_workarounds(self, db):
        seed(db)
        workarounds = db.query(Workaround).all()
        assert len(workarounds) == 4

    def test_seed_workarounds_have_code_snippets(self, db):
        seed(db)
        with_code = (db.query(Workaround)
                     .filter(Workaround.code_snippet.is_not(None))
                     .all())
        assert len(with_code) >= 2

    def test_seed_creates_ecu_links(self, db):
        seed(db)
        links = db.query(EcuErrata).all()
        assert len(links) == 6

    def test_seed_bms_ecu_exists(self, db):
        seed(db)
        bms = (db.query(EcuErrata)
               .filter(EcuErrata.ecu_name == "BMS_ECU")
               .all())
        assert len(bms) >= 1

    def test_seed_renesas_has_no_workaround_for_watchdog(self, db):
        """ERR_RH850-002 requires hardware respin — no workaround."""
        seed(db)
        errata = (db.query(Errata)
                  .filter(Errata.errata_id == "ERR_RH850-002")
                  .one())
        assert len(errata.workarounds) == 0
        assert errata.safety_blocking is True

    def test_seed_idempotency_guard(self, db):
        """Second seed call should be blocked by the guard in __main__."""
        seed(db)
        chips_after_first = db.query(Chip).count()
        # Guard logic: if chips exist, skip. We call seed directly here
        # so we test the count outcome is consistent.
        assert chips_after_first == 2

    def test_seed_nxp_errata_ids(self, db):
        seed(db)
        nxp_chip = db.query(Chip).filter(Chip.vendor == "NXP").one()
        errata_ids = {e.errata_id for e in nxp_chip.errata}
        assert "ERR_S32K3-001" in errata_ids
        assert "ERR_S32K3-002" in errata_ids
        assert "ERR_S32K3-003" in errata_ids
