"""
Seed script: populates the database with realistic errata records.
Run with: python scripts/seed.py

Chip coverage:
  - NXP S32K344 Rev B  (automotive MCU, used in BMS / Gateway ECUs)
  - Renesas RH850/U2A Rev 1.1  (ASIL-D MCU, used in ADAS / EPS ECUs)
"""
import os
import sys

# Allow running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import engine, Base, SessionLocal
from app.models.chip import Chip
from app.models.errata import Errata, SeverityEnum, MitigationTypeEnum, StatusEnum
from app.models.workaround import Workaround
from app.models.ecu_errata import EcuErrata


def create_tables():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
    print("[db] Tables created / verified.")


def seed(db):
    # ------------------------------------------------------------------ #
    # Chips                                                                 #
    # ------------------------------------------------------------------ #
    s32k344 = Chip(
        vendor="NXP",
        family="S32K344",
        revision="B",
        description="Automotive-grade 32-bit MCU, Cortex-M7, ASIL-B capable. "
                    "Widely used in body control, BMS, and gateway ECUs.",
        datasheet_url="https://www.nxp.com/products/processors-and-microcontrollers/"
                      "s32k-automotive-mcus/s32k3-microcontrollers-for-automotive-networking",
    )

    rh850 = Chip(
        vendor="Renesas",
        family="RH850/U2A",
        revision="1.1",
        description="ASIL-D 32-bit MCU for safety-critical automotive applications. "
                    "Used in ADAS and EPS systems.",
        datasheet_url="https://www.renesas.com/products/microcontrollers-microprocessors/"
                      "rh850-automotive/rh850u2a-automotive-mcu",
    )

    db.add_all([s32k344, rh850])
    db.flush()  # get IDs without committing
    print(f"[seed] Chip: {s32k344}")
    print(f"[seed] Chip: {rh850}")

    # ------------------------------------------------------------------ #
    # NXP S32K344 Errata                                                   #
    # ------------------------------------------------------------------ #

    # 1. CAN FD frame corruption
    e1 = Errata(
        chip_id=s32k344.id,
        errata_id="ERR_S32K3-001",
        title="CAN FD: Frame corruption under high bus load with ISO mode enabled",
        description=(
            "Under sustained high bus load (>70% utilisation) with CAN FD ISO mode enabled, "
            "the FlexCAN peripheral may corrupt the last byte of a data frame. "
            "Affected bit rate: 5 Mbit/s. Root cause: internal FIFO timing race in the "
            "message buffer arbitration logic. Observed on Rev B silicon only."
        ),
        severity=SeverityEnum.critical,
        mitigation_type=MitigationTypeEnum.software,
        status=StatusEnum.mitigated,
        safety_blocking=True,
        affected_silicon_revisions="B",
        source_url="https://www.nxp.com/docs/en/errata/S32K3_Rev_B_Errata.pdf",
        parsed_by_ai=False,
    )

    w1 = Workaround(
        errata_id=0,  # set below after flush
        description=(
            "Disable ISO mode (set CTRL2[ISOCANFDEN]=0) when bus load exceeds 60%. "
            "Alternatively, reduce nominal bit rate to 2 Mbit/s. "
            "A permanent fix is planned in Rev C silicon."
        ),
        code_snippet=(
            "/* S32K344 FlexCAN — disable ISO CAN FD mode */\n"
            "CAN0->CTRL2 &= ~CAN_CTRL2_ISOCANFDEN_MASK;"
        ),
        author="NXP Application Engineering",
    )

    # 2. ADC cross-talk
    e2 = Errata(
        chip_id=s32k344.id,
        errata_id="ERR_S32K3-002",
        title="ADC: Cross-talk between channels when sampling rate exceeds 1 MSPS",
        description=(
            "When two ADC channels on the same SAR module are sampled back-to-back "
            "at rates above 1 MSPS, approximately 0.8 LSB of cross-talk is induced. "
            "Impact is below 12-bit resolution threshold but visible at 16-bit."
        ),
        severity=SeverityEnum.medium,
        mitigation_type=MitigationTypeEnum.software,
        status=StatusEnum.verified,
        safety_blocking=False,
        affected_silicon_revisions="A, B",
        source_url="https://www.nxp.com/docs/en/errata/S32K3_Rev_B_Errata.pdf",
        parsed_by_ai=False,
    )

    w2 = Workaround(
        errata_id=0,
        description=(
            "Insert a 2-cycle pause between channel conversions by setting "
            "ADC_CFG1[ADIV] to divide clock by 4. Verified to eliminate cross-talk."
        ),
        code_snippet=(
            "/* S32K344 ADC — add inter-channel pause */\n"
            "ADC0->CFG1 = (ADC0->CFG1 & ~ADC_CFG1_ADIV_MASK)\n"
            "           | ADC_CFG1_ADIV(2);  /* divide by 4 */"
        ),
        author="NXP Application Engineering",
    )

    # 3. Flash ECC silent data corruption
    e3 = Errata(
        chip_id=s32k344.id,
        errata_id="ERR_S32K3-003",
        title="Flash: ECC single-bit error not reported after partial programming",
        description=(
            "Following a partial flash programming operation (< 128-bit aligned write), "
            "subsequent reads from the affected phrase may not trigger the ECC single-bit "
            "correction interrupt. The data returned is corrected silently, but the "
            "FCCU fault is not raised. This masks potential memory degradation."
        ),
        severity=SeverityEnum.high,
        mitigation_type=MitigationTypeEnum.software,
        status=StatusEnum.triaged,
        safety_blocking=True,
        affected_silicon_revisions="B",
        source_url="https://www.nxp.com/docs/en/errata/S32K3_Rev_B_Errata.pdf",
        parsed_by_ai=False,
    )

    w3 = Workaround(
        errata_id=0,
        description=(
            "Always perform 128-bit aligned flash writes. Use the HSE firmware's "
            "secure flash programming service instead of direct register access. "
            "Implement a periodic ECC scrub routine as compensating measure."
        ),
        code_snippet=None,
        author="OEM Safety Team",
    )

    db.add_all([e1, e2, e3])
    db.flush()

    # Fix workaround FK references now that errata IDs are assigned
    w1.errata_id = e1.id
    w2.errata_id = e2.id
    w3.errata_id = e3.id
    db.add_all([w1, w2, w3])

    # ECU links for NXP errata
    db.add_all([
        EcuErrata(errata_id=e1.id, ecu_name="BMS_ECU",
                  ecu_project="EV Platform Gen2",
                  notes="Workaround applied in CAN driver v2.3.1. Pending safety sign-off."),
        EcuErrata(errata_id=e1.id, ecu_name="Gateway_ECU",
                  ecu_project="EV Platform Gen2",
                  notes="ISO mode not used in gateway; not affected."),
        EcuErrata(errata_id=e2.id, ecu_name="BMS_ECU",
                  ecu_project="EV Platform Gen2",
                  notes="ADC clock divider applied. Verified by HIL test TS-ADC-112."),
        EcuErrata(errata_id=e3.id, ecu_name="BMS_ECU",
                  ecu_project="EV Platform Gen2",
                  notes="Flash writes audited. All writes now 128-bit aligned. Under review."),
    ])

    print(f"[seed] Errata (NXP): {e1.errata_id}, {e2.errata_id}, {e3.errata_id}")

    # ------------------------------------------------------------------ #
    # Renesas RH850/U2A Errata                                             #
    # ------------------------------------------------------------------ #

    # 4. LIN communication glitch
    e4 = Errata(
        chip_id=rh850.id,
        errata_id="ERR_RH850-001",
        title="RLIN3: Break field too short when baud rate divisor is odd",
        description=(
            "When the RLIN3 baud rate is configured with an odd prescaler divisor, "
            "the break field generated during LIN master mode is 12 bit-times instead "
            "of the required 13+. Some slave nodes reject the frame causing "
            "communication failures on LIN subnets."
        ),
        severity=SeverityEnum.high,
        mitigation_type=MitigationTypeEnum.software,
        status=StatusEnum.mitigated,
        safety_blocking=False,
        affected_silicon_revisions="1.0, 1.1",
        source_url="https://www.renesas.com/us/en/document/eln/rh850u2a-errata-notes",
        parsed_by_ai=False,
    )

    w4 = Workaround(
        errata_id=0,
        description=(
            "Use only even prescaler values for RLIN3. Adjust system clock or "
            "LIN target baud rate to ensure the divisor is always even. "
            "Updated RLIN3 driver included in BSP v3.2."
        ),
        code_snippet=(
            "/* Ensure RLIN3 prescaler is even */\n"
            "uint32_t div = RLIN3_CalcBaudDiv(target_baud);\n"
            "if (div & 1U) div++;  /* round up to next even */\n"
            "RLIN30.LWBR = (uint8_t)(div - 1U);"
        ),
        author="Renesas FAE",
    )

    # 5. Watchdog counter stall
    e5 = Errata(
        chip_id=rh850.id,
        errata_id="ERR_RH850-002",
        title="WDTA: Watchdog counter stalls when OSTM interrupt latency exceeds 3 cycles",
        description=(
            "Under heavy interrupt load, if the OS timer interrupt (OSTM) is delayed "
            "by more than 3 clock cycles, the WDTA down-counter halts rather than "
            "decrementing. A reset is not triggered — the counter simply freezes. "
            "This defeats the watchdog safety function entirely for the duration of "
            "the latency spike."
        ),
        severity=SeverityEnum.critical,
        mitigation_type=MitigationTypeEnum.hardware,
        status=StatusEnum.detected,
        safety_blocking=True,
        affected_silicon_revisions="1.1",
        source_url="https://www.renesas.com/us/en/document/eln/rh850u2a-errata-notes",
        parsed_by_ai=False,
    )
    # No workaround — hardware respin required

    db.add_all([e4, e5])
    db.flush()

    w4.errata_id = e4.id
    db.add(w4)

    db.add_all([
        EcuErrata(errata_id=e4.id, ecu_name="EPS_ECU",
                  ecu_project="Steering System X1",
                  notes="Updated LIN driver deployed. Integration test PASS."),
        EcuErrata(errata_id=e5.id, ecu_name="ADAS_ECU",
                  ecu_project="ADAS Platform V3",
                  notes="Hardware respin required. Blocking Rev 2.0 tape-out sign-off."),
    ])

    print(f"[seed] Errata (Renesas): {e4.errata_id}, {e5.errata_id}")

    db.commit()
    print("\n[seed] Done. Database seeded successfully.")
    print(f"       Chips: 2  |  Errata: 5  |  Workarounds: 4  |  ECU links: 6")


if __name__ == "__main__":
    create_tables()
    db = SessionLocal()
    try:
        # Avoid re-seeding on repeated runs
        if db.query(Chip).count() > 0:
            print("[seed] Database already has data — skipping. Delete the DB to re-seed.")
        else:
            seed(db)
    finally:
        db.close()
