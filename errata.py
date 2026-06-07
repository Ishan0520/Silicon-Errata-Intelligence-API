import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class SeverityEnum(str, enum.Enum):
    """Impact severity of the errata on system behavior."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class MitigationTypeEnum(str, enum.Enum):
    """
    How the errata can be resolved:
    - software: a code workaround exists (register config, driver patch, etc.)
    - hardware: requires a silicon respin or board-level rework
    - none: no mitigation currently available
    """
    software = "software"
    hardware = "hardware"
    none = "none"


class StatusEnum(str, enum.Enum):
    """
    Lifecycle state of an errata record.
    Flow: detected → triaged → mitigated → verified → closed
    """
    detected = "detected"
    triaged = "triaged"
    mitigated = "mitigated"
    verified = "verified"
    closed = "closed"


class Errata(Base):
    """
    A single known silicon bug published by the chip vendor.

    errata_id is the vendor's own identifier (e.g. "ERR-042", "e5234").
    safety_blocking flags errata that must be resolved before a safety cert (ISO 26262, IEC 61508).
    parsed_by_ai distinguishes auto-ingested records from manually verified ones.
    """
    __tablename__ = "errata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chip_id: Mapped[int] = mapped_column(ForeignKey("chips.id"), nullable=False, index=True)

    # Vendor-assigned errata identifier
    errata_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification fields
    severity: Mapped[SeverityEnum] = mapped_column(
        SAEnum(SeverityEnum, native_enum=False), nullable=False, index=True
    )
    mitigation_type: Mapped[MitigationTypeEnum] = mapped_column(
        SAEnum(MitigationTypeEnum, native_enum=False), nullable=False
    )
    status: Mapped[StatusEnum] = mapped_column(
        SAEnum(StatusEnum, native_enum=False),
        nullable=False,
        default=StatusEnum.detected,
        index=True,
    )

    # Safety certification flag — critical for automotive OEMs
    safety_blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Traceability
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    parsed_by_ai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    affected_silicon_revisions: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
        doc="Comma-separated list of affected revisions, e.g. 'A, B, B1'"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    chip: Mapped["Chip"] = relationship("Chip", back_populates="errata")  # noqa: F821
    workarounds: Mapped[list["Workaround"]] = relationship(  # noqa: F821
        "Workaround", back_populates="errata", cascade="all, delete-orphan"
    )
    ecu_links: Mapped[list["EcuErrata"]] = relationship(  # noqa: F821
        "EcuErrata", back_populates="errata", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Errata id={self.errata_id!r} severity={self.severity!r} "
            f"status={self.status!r} safety_blocking={self.safety_blocking}>"
        )
