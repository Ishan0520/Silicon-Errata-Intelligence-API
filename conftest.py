"""
Test configuration.

Uses an in-memory SQLite database so tests run without Docker or Postgres.
The DATABASE_URL env var is overridden before any app module is imported,
so the engine is created against SQLite.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Override before any app import touches the env var
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db.database import Base  # noqa: E402
from app.models import Chip, Errata, Workaround, EcuErrata  # noqa: E402, F401
from app.models.errata import SeverityEnum, MitigationTypeEnum, StatusEnum  # noqa: E402


TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db():
    """
    Yields a fresh database session with all tables created.
    Drops everything after each test so tests are fully isolated.
    """
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def sample_chip(db):
    """A seeded NXP S32K344 chip ready for use in tests."""
    chip = Chip(
        vendor="NXP",
        family="S32K344",
        revision="B",
        description="Test chip fixture",
    )
    db.add(chip)
    db.commit()
    db.refresh(chip)
    return chip


@pytest.fixture
def sample_errata(db, sample_chip):
    """A seeded critical errata linked to the sample chip."""
    errata = Errata(
        chip_id=sample_chip.id,
        errata_id="ERR_TEST-001",
        title="Test errata: CAN FD corruption",
        description="Detailed description of the CAN FD bug for testing.",
        severity=SeverityEnum.critical,
        mitigation_type=MitigationTypeEnum.software,
        status=StatusEnum.mitigated,
        safety_blocking=True,
    )
    db.add(errata)
    db.commit()
    db.refresh(errata)
    return errata
