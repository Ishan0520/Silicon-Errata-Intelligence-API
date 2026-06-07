from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class EcuErrata(Base):
    """
    Links a specific ECU (Electronic Control Unit) to an errata record.

    An OEM may run the same chip in dozens of ECUs. This table tracks
    which ECUs are affected by which errata and their per-ECU status.

    Example: NXP S32K344 Rev B used in both BMS and Gateway ECUs.
    The Gateway may have already applied a software workaround; BMS may not.
    """
    __tablename__ = "ecu_errata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    errata_id: Mapped[int] = mapped_column(ForeignKey("errata.id"), nullable=False, index=True)

    # ECU identification — plain strings; no separate ECU table to keep it simple
    ecu_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    ecu_project: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Per-ECU mitigation notes (may differ from the global errata status)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    errata: Mapped["Errata"] = relationship("Errata", back_populates="ecu_links")  # noqa: F821

    def __repr__(self) -> str:
        return f"<EcuErrata ecu={self.ecu_name!r} errata_id={self.errata_id}>"
