"""Export and import functionality for expenses."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from sqlite3 import Connection

from expense_tracker.database import add_expense, list_expenses
from expense_tracker.date_utils import parse_date


def export_csv(conn: Connection, output_path: str) -> int:
    """Export all expenses to CSV. Returns the number of rows exported."""
    expenses = list_expenses(conn)
    path = Path(output_path)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "amount", "category", "note", "date", "created_at", "updated_at"])
        for exp in expenses:
            writer.writerow([
                exp.id, exp.amount, exp.category, exp.note,
                exp.date.isoformat(), exp.created_at.isoformat(), exp.updated_at.isoformat(),
            ])

    return len(expenses)


def export_json(conn: Connection, output_path: str) -> int:
    """Export all expenses to JSON. Returns the number of rows exported."""
    expenses = list_expenses(conn)
    data = [exp.to_dict() for exp in expenses]

    with Path(output_path).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return len(expenses)


def import_csv(conn: Connection, input_path: str) -> int:
    """Import expenses from CSV. Returns the number of rows imported."""
    count = 0
    with Path(input_path).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            add_expense(
                conn,
                amount=float(row["amount"]),
                category=row["category"],
                note=row.get("note", ""),
                date=parse_date(row["date"]),
            )
            count += 1
    return count
