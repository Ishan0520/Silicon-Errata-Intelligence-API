from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Chip(Base):
    """
    Represents a specific silicon chip family + revision.

    Example: NXP S32K344 Rev B, Renesas RH850/U2A Rev 1.1
    A single chip family may have multiple revisions, each with its own errata.
    """
    __tablename__ = "chips"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    family: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    revision: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    datasheet_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    errata: Mapped[list["Errata"]] = relationship(  # noqa: F821
        "Errata", back_populates="chip", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Chip vendor={self.vendor!r} family={self.family!r} rev={self.revision!r}>"
