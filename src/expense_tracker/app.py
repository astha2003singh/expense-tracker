"""Flask web application for the Expense Tracker dashboard."""

from __future__ import annotations

import json
from datetime import datetime

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, render_template, request

from expense_tracker import database as db
from expense_tracker.pdf_parser import extract_expenses_from_pdf


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(
            __import__("pathlib").Path(__file__).parent / "templates"
        ),
        static_folder=str(
            __import__("pathlib").Path(__file__).parent / "static"
        ),
    )

    # ── Initialize DB on first request ───────────────────────────────────

    @app.before_request
    def _ensure_db():
        if not hasattr(app, "_db_initialized"):
            conn = db.get_connection()
            db.init_db(conn)
            conn.close()
            app._db_initialized = True

    # ── Pages ─────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("dashboard.html")

    # ── API Routes ────────────────────────────────────────────────────────

    @app.route("/api/stats")
    def api_stats():
        """Get dashboard statistics."""
        conn = db.get_connection()
        now = datetime.now()

        total_all = db.get_total_expenses(conn)
        total_month = db.get_monthly_total(conn, now.month, now.year)
        expense_count = db.get_expense_count(conn)

        # Budget info
        overall_budget = db.get_budget(conn, now.month, now.year)
        budget_amount = overall_budget.amount if overall_budget else 0
        budget_remaining = budget_amount - total_month if overall_budget else 0

        conn.close()
        return jsonify({
            "total_all_time": total_all,
            "total_this_month": total_month,
            "expense_count": expense_count,
            "budget_amount": budget_amount,
            "budget_remaining": budget_remaining,
            "budget_set": overall_budget is not None,
            "current_month": now.strftime("%B %Y"),
        })

    @app.route("/api/expenses")
    def api_expenses():
        """Get expenses with optional filters."""
        conn = db.get_connection()
        category = request.args.get("category")
        month = request.args.get("month", type=int)
        year = request.args.get("year", type=int)
        limit = request.args.get("limit", 20, type=int)

        expenses = db.list_expenses(conn, category=category, month=month, year=year, limit=limit)
        conn.close()

        return jsonify([exp.to_dict() for exp in expenses])

    @app.route("/api/expenses", methods=["POST"])
    def api_add_expense():
        """Add a new expense."""
        data = request.get_json()
        conn = db.get_connection()

        try:
            amount = float(data["amount"])
            category = data["category"]
            note = data.get("note", "")
            date_str = data.get("date")

            expense_date = None
            if date_str:
                from expense_tracker.date_utils import parse_date
                expense_date = parse_date(date_str)

            expense = db.add_expense(conn, amount, category, note, expense_date)
            conn.close()
            return jsonify(expense.to_dict()), 201
        except (ValueError, KeyError) as e:
            conn.close()
            return jsonify({"error": str(e)}), 400

    @app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
    def api_delete_expense(expense_id):
        """Delete an expense."""
        conn = db.get_connection()
        if db.delete_expense(conn, expense_id):
            conn.close()
            return jsonify({"success": True})
        conn.close()
        return jsonify({"error": "Not found"}), 404

    @app.route("/api/categories")
    def api_categories():
        """Get all categories with colors."""
        conn = db.get_connection()
        categories = db.list_categories(conn)
        conn.close()
        return jsonify([
            {"id": c.id, "name": c.name, "is_default": c.is_default, "color": c.color}
            for c in categories
        ])

    @app.route("/api/category-totals")
    def api_category_totals():
        """Get spending by category."""
        conn = db.get_connection()
        month = request.args.get("month", type=int)
        year = request.args.get("year", type=int)
        totals = db.get_category_totals(conn, month, year)
        colors = db.get_category_colors(conn)
        conn.close()
        return jsonify([
            {"category": cat, "total": total, "color": colors.get(cat, "#868e96")}
            for cat, total in totals
        ])

    @app.route("/api/monthly-totals")
    def api_monthly_totals():
        """Get monthly spending trend."""
        conn = db.get_connection()
        num = request.args.get("months", 6, type=int)
        totals = db.get_monthly_totals(conn, num)
        conn.close()
        return jsonify([{"month": m, "total": t} for m, t in totals])

    @app.route("/api/daily-totals")
    def api_daily_totals():
        """Get daily spending for current month."""
        conn = db.get_connection()
        now = datetime.now()
        month = request.args.get("month", now.month, type=int)
        year = request.args.get("year", now.year, type=int)
        totals = db.get_daily_totals(conn, month, year)
        conn.close()
        return jsonify([{"day": d, "total": t} for d, t in totals])

    @app.route("/api/budgets")
    def api_budgets():
        """Get budgets for current month."""
        conn = db.get_connection()
        now = datetime.now()
        month = request.args.get("month", now.month, type=int)
        year = request.args.get("year", now.year, type=int)
        budgets = db.get_budgets_for_month(conn, month, year)

        result = []
        for b in budgets:
            spent = db.get_monthly_total(conn, month, year, b.category)
            result.append({
                "id": b.id,
                "category": b.category or "Overall",
                "amount": b.amount,
                "spent": spent,
                "remaining": b.amount - spent,
                "percentage": (spent / b.amount * 100) if b.amount > 0 else 0,
            })

        conn.close()
        return jsonify(result)

    @app.route("/api/budget", methods=["POST"])
    def api_set_budget():
        """Set a budget."""
        data = request.get_json()
        conn = db.get_connection()
        now = datetime.now()

        try:
            amount = float(data["amount"])
            month = data.get("month", now.month)
            year = data.get("year", now.year)
            category = data.get("category") or None

            budget = db.set_budget(conn, amount, month, year, category)
            conn.close()
            return jsonify({
                "id": budget.id,
                "category": budget.category or "Overall",
                "amount": budget.amount,
                "month": budget.month,
                "year": budget.year,
            }), 201
        except (ValueError, KeyError) as e:
            conn.close()
            return jsonify({"error": str(e)}), 400

    @app.route("/api/upload-pdf", methods=["POST"])
    def api_upload_pdf():
        """Upload a PDF bank statement."""
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            import pathlib
            upload_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            filepath = upload_dir / filename
            file.save(filepath)
            
            conn = db.get_connection()
            try:
                count = extract_expenses_from_pdf(filepath, conn)
                conn.close()
                return jsonify({"success": True, "count": count})
            except Exception as e:
                conn.close()
                return jsonify({"error": str(e)}), 500
                
        return jsonify({"error": "Invalid file format, must be PDF"}), 400

    return app
