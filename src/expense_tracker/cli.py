"""CLI interface for the Expense Tracker using Click."""

from __future__ import annotations

from datetime import datetime

import click

from expense_tracker import database as db
from expense_tracker.date_utils import parse_date
from expense_tracker.display import (
    console,
    display_budget_status,
    display_categories,
    display_category_breakdown,
    display_expenses,
    error,
    success,
    warning,
)
from expense_tracker.export import export_csv, export_json, import_csv


def _get_conn():
    """Get an initialized database connection."""
    conn = db.get_connection()
    db.init_db(conn)
    return conn


# ── Main CLI group ───────────────────────────────────────────────────────────


@click.group()
@click.version_option(version="1.0.0", prog_name="Expense Tracker")
def cli():
    """💰 Expense Tracker — Track, budget, and analyze your expenses."""
    pass


# ── Expense commands ─────────────────────────────────────────────────────────


@cli.command()
@click.option("--amount", "-a", type=float, required=True, help="Expense amount")
@click.option("--category", "-c", type=str, required=True, help="Expense category")
@click.option("--note", "-n", type=str, default="", help="Optional note")
@click.option("--date", "-d", "date_str", type=str, default=None, help="Date (YYYY-MM-DD or 'today', 'yesterday')")
def add(amount: float, category: str, note: str, date_str: str | None):
    """Add a new expense."""
    conn = _get_conn()

    if amount <= 0:
        error("Amount must be positive.")
        return

    expense_date = None
    if date_str:
        try:
            expense_date = parse_date(date_str)
        except ValueError as e:
            error(str(e))
            return

    expense = db.add_expense(conn, amount, category, note, expense_date)
    success(f"Added expense #{expense.id}: ₹{amount:,.2f} [{category}]")

    # Check budget
    now = expense.date
    budget = db.get_budget(conn, now.month, now.year, category)
    if budget:
        spent = db.get_monthly_total(conn, now.month, now.year, category)
        pct = spent / budget.amount * 100
        if pct >= 100:
            warning(f"Budget EXCEEDED for {category}! Spent ₹{spent:,.2f} / ₹{budget.amount:,.2f}")
        elif pct >= 80:
            warning(f"Budget warning for {category}: {pct:.0f}% used (₹{spent:,.2f} / ₹{budget.amount:,.2f})")

    overall = db.get_budget(conn, now.month, now.year)
    if overall:
        total_spent = db.get_monthly_total(conn, now.month, now.year)
        pct = total_spent / overall.amount * 100
        if pct >= 100:
            warning(f"Overall budget EXCEEDED! Spent ₹{total_spent:,.2f} / ₹{overall.amount:,.2f}")
        elif pct >= 80:
            warning(f"Overall budget warning: {pct:.0f}% used (₹{total_spent:,.2f} / ₹{overall.amount:,.2f})")

    conn.close()


@cli.command(name="list")
@click.option("--category", "-c", type=str, default=None, help="Filter by category")
@click.option("--month", "-m", type=int, default=None, help="Filter by month (1-12)")
@click.option("--year", "-y", type=int, default=None, help="Filter by year")
@click.option("--limit", "-l", type=int, default=None, help="Limit number of results")
def list_cmd(category: str | None, month: int | None, year: int | None, limit: int | None):
    """List expenses with optional filters."""
    conn = _get_conn()
    expenses = db.list_expenses(conn, category=category, month=month, year=year, limit=limit)

    title = "All Expenses"
    parts = []
    if category:
        parts.append(f"Category: {category}")
    if month:
        parts.append(f"Month: {month}")
    if year:
        parts.append(f"Year: {year}")
    if parts:
        title = "Expenses — " + ", ".join(parts)

    display_expenses(expenses, title)
    conn.close()


@cli.command()
@click.argument("expense_id", type=int)
@click.option("--amount", "-a", type=float, default=None, help="New amount")
@click.option("--category", "-c", type=str, default=None, help="New category")
@click.option("--note", "-n", type=str, default=None, help="New note")
@click.option("--date", "-d", "date_str", type=str, default=None, help="New date")
def edit(expense_id: int, amount: float | None, category: str | None, note: str | None, date_str: str | None):
    """Edit an existing expense by ID."""
    conn = _get_conn()

    expense_date = None
    if date_str:
        try:
            expense_date = parse_date(date_str)
        except ValueError as e:
            error(str(e))
            return

    updated = db.update_expense(conn, expense_id, amount, category, note, expense_date)
    if updated:
        success(f"Updated expense #{expense_id}")
        display_expenses([updated])
    else:
        error(f"Expense #{expense_id} not found.")

    conn.close()


@cli.command()
@click.argument("expense_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(expense_id: int, yes: bool):
    """Delete an expense by ID."""
    conn = _get_conn()

    if not yes:
        expense = db.get_expense(conn, expense_id)
        if not expense:
            error(f"Expense #{expense_id} not found.")
            conn.close()
            return
        console.print(f"  Delete expense #{expense_id}: ₹{expense.amount:,.2f} [{expense.category}]?")
        if not click.confirm("  Confirm?"):
            console.print("[dim]Cancelled.[/dim]")
            conn.close()
            return

    if db.delete_expense(conn, expense_id):
        success(f"Deleted expense #{expense_id}")
    else:
        error(f"Expense #{expense_id} not found.")

    conn.close()


# ── Category commands ────────────────────────────────────────────────────────


@cli.group()
def category():
    """Manage expense categories."""
    pass


@category.command(name="list")
def category_list():
    """List all categories."""
    conn = _get_conn()
    categories = db.list_categories(conn)
    display_categories(categories)
    conn.close()


@category.command(name="add")
@click.argument("name")
@click.option("--color", "-c", default="#868e96", help="Category color (hex)")
def category_add(name: str, color: str):
    """Add a custom category."""
    conn = _get_conn()
    cat = db.add_category(conn, name, color)
    if cat:
        success(f"Added category '{name}'")
    else:
        error(f"Category '{name}' already exists.")
    conn.close()


@category.command(name="remove")
@click.argument("name")
def category_remove(name: str):
    """Remove a custom category."""
    conn = _get_conn()
    if db.delete_category(conn, name):
        success(f"Removed category '{name}'")
    else:
        error(f"Cannot remove '{name}' (not found or is a default category).")
    conn.close()


# ── Budget commands ──────────────────────────────────────────────────────────


@cli.group()
def budget():
    """Manage monthly budgets."""
    pass


@budget.command(name="set")
@click.option("--amount", "-a", type=float, required=True, help="Budget amount")
@click.option("--month", "-m", type=int, default=None, help="Month (1-12, default: current)")
@click.option("--year", "-y", type=int, default=None, help="Year (default: current)")
@click.option("--category", "-c", type=str, default=None, help="Category (omit for overall)")
def budget_set(amount: float, month: int | None, year: int | None, category: str | None):
    """Set a monthly budget."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    conn = _get_conn()
    budget_obj = db.set_budget(conn, amount, month, year, category)
    label = category or "Overall"
    success(f"Set {label} budget for {month}/{year}: ₹{amount:,.2f}")
    conn.close()


@budget.command(name="status")
@click.option("--month", "-m", type=int, default=None, help="Month (default: current)")
@click.option("--year", "-y", type=int, default=None, help="Year (default: current)")
def budget_status(month: int | None, year: int | None):
    """Show budget status for a month."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    conn = _get_conn()
    budgets = db.get_budgets_for_month(conn, month, year)

    if not budgets:
        warning(f"No budgets set for {month}/{year}.")
        conn.close()
        return

    for b in budgets:
        spent = db.get_monthly_total(conn, month, year, b.category)
        display_budget_status(b, spent)

    conn.close()


# ── Report commands ──────────────────────────────────────────────────────────


@cli.group()
def report():
    """Generate spending reports."""
    pass


@report.command(name="summary")
@click.option("--month", "-m", type=int, default=None, help="Month (default: current)")
@click.option("--year", "-y", type=int, default=None, help="Year (default: current)")
def report_summary(month: int | None, year: int | None):
    """Show monthly spending summary."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    conn = _get_conn()
    total = db.get_monthly_total(conn, month, year)
    totals = db.get_category_totals(conn, month, year)

    console.print(f"\n[bold]Monthly Summary — {month}/{year}[/bold]")
    console.print(f"Total Spending: [bold green]₹{total:,.2f}[/bold green]\n")

    display_category_breakdown(totals, f"Breakdown — {month}/{year}")
    conn.close()


@report.command(name="trend")
@click.option("--months", "-n", type=int, default=6, help="Number of months to show")
def report_trend(months: int):
    """Show spending trend over recent months."""
    conn = _get_conn()
    monthly = db.get_monthly_totals(conn, months)

    if not monthly:
        warning("No data to show.")
        conn.close()
        return

    from rich.table import Table

    table = Table(title=f"Spending Trend (Last {months} months)", border_style="dim")
    table.add_column("Month", style="cyan")
    table.add_column("Total", style="green", justify="right")
    table.add_column("Trend", min_width=25)

    max_amount = max(amount for _, amount in monthly) if monthly else 1
    for month_str, amount in monthly:
        bar_len = int(amount / max_amount * 25)
        bar = "█" * bar_len
        table.add_row(month_str, f"₹{amount:,.2f}", f"[cyan]{bar}[/cyan]")

    console.print(table)
    conn.close()


# ── Export commands ───────────────────────────────────────────────────────────


@cli.group()
def export():
    """Export or import expense data."""
    pass


@export.command(name="csv")
@click.option("--output", "-o", type=str, default="expenses.csv", help="Output file path")
def export_csv_cmd(output: str):
    """Export expenses to CSV."""
    conn = _get_conn()
    count = export_csv(conn, output)
    success(f"Exported {count} expenses to {output}")
    conn.close()


@export.command(name="json")
@click.option("--output", "-o", type=str, default="expenses.json", help="Output file path")
def export_json_cmd(output: str):
    """Export expenses to JSON."""
    conn = _get_conn()
    count = export_json(conn, output)
    success(f"Exported {count} expenses to {output}")
    conn.close()


@export.command(name="import")
@click.argument("file", type=click.Path(exists=True))
def import_cmd(file: str):
    """Import expenses from a CSV file."""
    conn = _get_conn()
    count = import_csv(conn, file)
    success(f"Imported {count} expenses from {file}")
    conn.close()


# ── Dashboard command ────────────────────────────────────────────────────────


@cli.command()
@click.option("--port", "-p", type=int, default=5000, help="Port to run dashboard on")
@click.option("--host", "-h", "host", type=str, default="127.0.0.1", help="Host to bind to")
def dashboard(port: int, host: str):
    """Launch the web dashboard."""
    from expense_tracker.app import create_app

    app = create_app()
    print(f"\n  Dashboard running at http://{host}:{port}\n")
    print("  Press Ctrl+C to stop.\n")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    cli()
