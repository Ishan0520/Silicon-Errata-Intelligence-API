from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Workaround(Base):
    """
    A mitigation step for a specific errata.

    One errata can have multiple workarounds (e.g. a quick software patch
    followed by a more thorough hardware fix in the next respin).
    code_snippet stores a small example — driver config, register write, etc.
    """
    __tablename__ = "workarounds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    errata_id: Mapped[int] = mapped_column(ForeignKey("errata.id"), nullable=False, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    code_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    errata: Mapped["Errata"] = relationship("Errata", back_populates="workarounds")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Workaround errata_id={self.errata_id} author={self.author!r}>"
