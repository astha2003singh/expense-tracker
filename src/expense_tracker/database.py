"""Database operations for the Expense Tracker."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from expense_tracker.models import Budget, Category, Expense

DEFAULT_CATEGORIES = [
    ("Food", True, "#ff6b6b"),
    ("Transport", True, "#ffd93d"),
    ("Entertainment", True, "#6bcb77"),
    ("Shopping", True, "#4d96ff"),
    ("Bills", True, "#ff922b"),
    ("Health", True, "#cc5de8"),
    ("Education", True, "#20c997"),
    ("Other", True, "#868e96"),
]


def get_db_path() -> Path:
    """Get the database file path (project-local)."""
    db_dir = Path(__file__).resolve().parent.parent.parent / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "expenses.db"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Create and return a database connection."""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema and seed default categories."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT DEFAULT '',
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_default INTEGER DEFAULT 0,
            color TEXT DEFAULT '#868e96'
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            amount REAL NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            UNIQUE(category, month, year)
        );

        CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
        CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
    """
    )

    # Seed default categories if empty
    cursor = conn.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO categories (name, is_default, color) VALUES (?, ?, ?)",
            DEFAULT_CATEGORIES,
        )
    conn.commit()


# ── Expense CRUD ─────────────────────────────────────────────────────────────


def add_expense(
    conn: sqlite3.Connection,
    amount: float,
    category: str,
    note: str = "",
    date: datetime | None = None,
) -> Expense:
    """Add a new expense and return it."""
    now = datetime.now()
    if date is None:
        date = now

    cursor = conn.execute(
        """INSERT INTO expenses (amount, category, note, date, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (amount, category, note, date.isoformat(), now.isoformat(), now.isoformat()),
    )
    conn.commit()
    return Expense(
        id=cursor.lastrowid,
        amount=amount,
        category=category,
        note=note,
        date=date,
        created_at=now,
        updated_at=now,
    )


def get_expense(conn: sqlite3.Connection, expense_id: int) -> Expense | None:
    """Get a single expense by ID."""
    cursor = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    row = cursor.fetchone()
    return Expense.from_row(row) if row else None


def list_expenses(
    conn: sqlite3.Connection,
    category: str | None = None,
    month: int | None = None,
    year: int | None = None,
    limit: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[Expense]:
    """List expenses with optional filters."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params: list = []

    if category:
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)
    if month and year:
        query += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.extend([f"{month:02d}", str(year)])
    elif month:
        query += " AND strftime('%m', date) = ?"
        params.append(f"{month:02d}")
    elif year:
        query += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor = conn.execute(query, params)
    return [Expense.from_row(row) for row in cursor.fetchall()]


def update_expense(
    conn: sqlite3.Connection,
    expense_id: int,
    amount: float | None = None,
    category: str | None = None,
    note: str | None = None,
    date: datetime | None = None,
) -> Expense | None:
    """Update an existing expense."""
    existing = get_expense(conn, expense_id)
    if not existing:
        return None

    now = datetime.now()
    new_amount = amount if amount is not None else existing.amount
    new_category = category if category is not None else existing.category
    new_note = note if note is not None else existing.note
    new_date = date if date is not None else existing.date

    conn.execute(
        """UPDATE expenses
           SET amount = ?, category = ?, note = ?, date = ?, updated_at = ?
           WHERE id = ?""",
        (
            new_amount,
            new_category,
            new_note,
            new_date.isoformat(),
            now.isoformat(),
            expense_id,
        ),
    )
    conn.commit()
    return get_expense(conn, expense_id)


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    """Delete an expense. Returns True if deleted."""
    cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cursor.rowcount > 0


# ── Category operations ──────────────────────────────────────────────────────


def list_categories(conn: sqlite3.Connection) -> list[Category]:
    """List all categories."""
    cursor = conn.execute("SELECT * FROM categories ORDER BY name")
    return [Category.from_row(row) for row in cursor.fetchall()]


def add_category(
    conn: sqlite3.Connection, name: str, color: str = "#868e96"
) -> Category | None:
    """Add a custom category. Returns None if it already exists."""
    try:
        cursor = conn.execute(
            "INSERT INTO categories (name, is_default, color) VALUES (?, 0, ?)",
            (name, color),
        )
        conn.commit()
        return Category(id=cursor.lastrowid, name=name, is_default=False, color=color)
    except sqlite3.IntegrityError:
        return None


def delete_category(conn: sqlite3.Connection, name: str) -> bool:
    """Delete a custom category (cannot delete defaults)."""
    cursor = conn.execute(
        "DELETE FROM categories WHERE name = ? AND is_default = 0", (name,)
    )
    conn.commit()
    return cursor.rowcount > 0


def get_category_colors(conn: sqlite3.Connection) -> dict[str, str]:
    """Get a mapping of category name -> color."""
    cursor = conn.execute("SELECT name, color FROM categories")
    return {row[0]: row[1] for row in cursor.fetchall()}


# ── Budget operations ────────────────────────────────────────────────────────


def set_budget(
    conn: sqlite3.Connection,
    amount: float,
    month: int,
    year: int,
    category: str | None = None,
) -> Budget:
    """Set or update a budget for a month (optionally per category)."""
    conn.execute(
        """INSERT INTO budgets (category, amount, month, year)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(category, month, year)
           DO UPDATE SET amount = excluded.amount""",
        (category, amount, month, year),
    )
    conn.commit()
    cursor = conn.execute(
        "SELECT * FROM budgets WHERE category IS ? AND month = ? AND year = ?",
        (category, month, year),
    )
    row = cursor.fetchone()
    return Budget.from_row(row)


def get_budget(
    conn: sqlite3.Connection,
    month: int,
    year: int,
    category: str | None = None,
) -> Budget | None:
    """Get budget for a specific month and optional category."""
    if category is None:
        cursor = conn.execute(
            "SELECT * FROM budgets WHERE category IS NULL AND month = ? AND year = ?",
            (month, year),
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM budgets WHERE category = ? AND month = ? AND year = ?",
            (category, month, year),
        )
    row = cursor.fetchone()
    return Budget.from_row(row) if row else None


def get_budgets_for_month(
    conn: sqlite3.Connection, month: int, year: int
) -> list[Budget]:
    """Get all budgets for a month."""
    cursor = conn.execute(
        "SELECT * FROM budgets WHERE month = ? AND year = ?",
        (month, year),
    )
    return [Budget.from_row(row) for row in cursor.fetchall()]


# ── Aggregation queries ──────────────────────────────────────────────────────


def get_monthly_total(
    conn: sqlite3.Connection, month: int, year: int, category: str | None = None
) -> float:
    """Get total spending for a month, optionally filtered by category."""
    query = """SELECT COALESCE(SUM(amount), 0) FROM expenses
               WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?"""
    params: list = [f"{month:02d}", str(year)]

    if category:
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)

    cursor = conn.execute(query, params)
    return cursor.fetchone()[0]


def get_category_totals(
    conn: sqlite3.Connection, month: int | None = None, year: int | None = None
) -> list[tuple[str, float]]:
    """Get spending totals by category."""
    query = "SELECT category, SUM(amount) FROM expenses WHERE 1=1"
    params: list = []

    if month and year:
        query += " AND strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params.extend([f"{month:02d}", str(year)])

    query += " GROUP BY category ORDER BY SUM(amount) DESC"
    cursor = conn.execute(query, params)
    return cursor.fetchall()


def get_monthly_totals(
    conn: sqlite3.Connection, num_months: int = 6
) -> list[tuple[str, float]]:
    """Get total spending per month for the last N months."""
    cursor = conn.execute(
        """SELECT strftime('%Y-%m', date) as month, SUM(amount)
           FROM expenses
           GROUP BY month
           ORDER BY month DESC
           LIMIT ?""",
        (num_months,),
    )
    return list(reversed(cursor.fetchall()))


def get_daily_totals(
    conn: sqlite3.Connection, month: int, year: int
) -> list[tuple[str, float]]:
    """Get daily spending totals for a specific month."""
    cursor = conn.execute(
        """SELECT strftime('%Y-%m-%d', date) as day, SUM(amount)
           FROM expenses
           WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
           GROUP BY day
           ORDER BY day""",
        (f"{month:02d}", str(year)),
    )
    return cursor.fetchall()


def get_total_expenses(conn: sqlite3.Connection) -> float:
    """Get the total of all expenses."""
    cursor = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
    return cursor.fetchone()[0]


def get_expense_count(conn: sqlite3.Connection) -> int:
    """Get total number of expenses."""
    cursor = conn.execute("SELECT COUNT(*) FROM expenses")
    return cursor.fetchone()[0]
