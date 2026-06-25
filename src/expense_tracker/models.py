"""Data models for the Expense Tracker application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Expense:
    """Represents a single expense entry."""

    id: int | None
    amount: float
    category: str
    note: str = ""
    date: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert expense to a dictionary for export."""
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "note": self.note,
            "date": self.date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: tuple) -> Expense:
        """Create an Expense from a database row."""
        return cls(
            id=row[0],
            amount=row[1],
            category=row[2],
            note=row[3],
            date=datetime.fromisoformat(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
        )


@dataclass
class Category:
    """Represents an expense category."""

    id: int | None
    name: str
    is_default: bool = False
    color: str = "white"

    @classmethod
    def from_row(cls, row: tuple) -> Category:
        """Create a Category from a database row."""
        return cls(
            id=row[0],
            name=row[1],
            is_default=bool(row[2]),
            color=row[3],
        )


@dataclass
class Budget:
    """Represents a budget for a month, optionally scoped to a category."""

    id: int | None
    category: str | None  # None = overall budget
    amount: float
    month: int
    year: int

    @classmethod
    def from_row(cls, row: tuple) -> Budget:
        """Create a Budget from a database row."""
        return cls(
            id=row[0],
            category=row[1],
            amount=row[2],
            month=row[3],
            year=row[4],
        )
