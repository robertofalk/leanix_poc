import datetime
from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class Base(DeclarativeBase):
    pass

class InventoryItem(Base):
    __tablename__ = "inventory_item"

    name: Mapped[str] = mapped_column(String(200), primary_key=True)
    description: Mapped[str] = mapped_column(String())
    provider: Mapped[str] = mapped_column(String(200))
    lifeciycle_status: Mapped[str] = mapped_column(String(100))
    revision: Mapped[int]
    source: Mapped[str] = mapped_column(String(200))
    new_name: Mapped[str] = mapped_column(String(200), nullable=True)
    last_update: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now)
    ref_text: Mapped[str] = mapped_column(String())
    # bleu_score: Mapped[float] = mapped_column(Numeric(precision=20, scale=16))
    # rouge_score: Mapped[float] = mapped_column(Numeric(precision=20, scale=16))
    meteor_score: Mapped[float] = mapped_column(Numeric(precision=20, scale=16))