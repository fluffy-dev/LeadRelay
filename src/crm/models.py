import enum
from datetime import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class CaseStatus(str, enum.Enum):
    """Status of a lead case."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class SourceOperatorLink(Base):
    """Association table between Source and Operator with weight configuration."""
    __tablename__ = "source_operator_links"

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), primary_key=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)

    operator: Mapped["Operator"] = relationship("Operator", back_populates="source_links")
    source: Mapped["Source"] = relationship("Source", back_populates="operator_links")


class Operator(Base):
    """Represents a support operator."""
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_load: Mapped[int] = mapped_column(Integer, default=10)

    source_links: Mapped[List["SourceOperatorLink"]] = relationship(
        "SourceOperatorLink", back_populates="operator"
    )
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="operator")


class Source(Base):
    """Represents a lead source (bot)."""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    operator_links: Mapped[List["SourceOperatorLink"]] = relationship(
        "SourceOperatorLink", back_populates="source"
    )


class Lead(Base):
    """Represents a unique client."""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identifier: Mapped[str] = mapped_column(String, unique=True, index=True)

    cases: Mapped[List["Case"]] = relationship("Case", back_populates="lead")


class Case(Base):
    """Represents a specific interaction/appeal from a lead."""
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.OPEN)

    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("operators.id"), nullable=True)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="cases")
    operator: Mapped["Operator"] = relationship("Operator", back_populates="cases")