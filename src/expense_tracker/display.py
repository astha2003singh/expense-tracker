"""Rich terminal display helpers."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from expense_tracker.models import Budget, Category, Expense

console = Console()


def display_expenses(expenses: list[Expense], title: str = "Expenses") -> None:
    """Display expenses in a rich table."""
    if not expenses:
        console.print(Panel("[dim]No expenses found.[/dim]", title=title))
        return

    table = Table(title=title, show_lines=False, border_style="dim")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Category", style="magenta", width=14)
    table.add_column("Amount", style="green", justify="right", width=12)
    table.add_column("Note", style="white", max_width=30)

    total = 0.0
    for exp in expenses:
        total += exp.amount
        table.add_row(
            str(exp.id),
            exp.date.strftime("%Y-%m-%d"),
            exp.category,
            f"₹{exp.amount:,.2f}",
            exp.note or "—",
        )

    table.add_section()
    table.add_row("", "", "[bold]Total[/bold]", f"[bold green]₹{total:,.2f}[/bold green]", "")

    console.print(table)


def display_categories(categories: list[Category]) -> None:
    """Display categories in a rich table."""
    table = Table(title="Categories", border_style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Color", style="white")

    for cat in categories:
        cat_type = "Default" if cat.is_default else "Custom"
        table.add_row(cat.name, cat_type, f"[{cat.color}]██[/{cat.color}] {cat.color}")

    console.print(table)


def display_budget_status(
    budget: Budget, spent: float
) -> None:
    """Display budget status with progress bar."""
    remaining = budget.amount - spent
    pct = (spent / budget.amount * 100) if budget.amount > 0 else 0

    label = budget.category or "Overall"

    if pct >= 100:
        color = "red"
        status = "🔴 EXCEEDED"
    elif pct >= 80:
        color = "yellow"
        status = "🟡 WARNING"
    else:
        color = "green"
        status = "🟢 ON TRACK"

    panel_content = Text()
    panel_content.append(f"Budget:    ₹{budget.amount:,.2f}\n")
    panel_content.append(f"Spent:     ₹{spent:,.2f}\n", style=color)
    panel_content.append(f"Remaining: ₹{remaining:,.2f}\n", style=color)
    panel_content.append(f"Usage:     {pct:.1f}%  {status}")

    console.print(
        Panel(panel_content, title=f"Budget — {label}", border_style=color)
    )


def display_category_breakdown(
    totals: list[tuple[str, float]], title: str = "Category Breakdown"
) -> None:
    """Display category spending breakdown."""
    if not totals:
        console.print(Panel("[dim]No data.[/dim]", title=title))
        return

    grand_total = sum(amount for _, amount in totals)
    table = Table(title=title, border_style="dim")
    table.add_column("Category", style="cyan")
    table.add_column("Amount", style="green", justify="right")
    table.add_column("Percentage", justify="right")
    table.add_column("Bar", min_width=20)

    for category, amount in totals:
        pct = (amount / grand_total * 100) if grand_total > 0 else 0
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        table.add_row(category, f"₹{amount:,.2f}", f"{pct:.1f}%", f"[magenta]{bar}[/magenta]")

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold green]₹{grand_total:,.2f}[/bold green]", "100%", "")

    console.print(table)


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")
