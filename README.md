# 💰 Python Expense Tracker

A robust, CLI-first expense tracking application built with Python. Designed for developers and power users, this tool helps you seamlessly manage your finances right from your terminal, while also offering a minimalistic web dashboard for visual analytics.

## 🚀 Key Features

* **Rich CLI Interface:** Fast, efficient, and beautifully formatted terminal commands powered by `Click` and `Rich`.
* **Smart Date Parsing:** Add expenses using standard ISO formats (YYYY-MM-DD) or natural language (like "today" or "yesterday").
* **Budget Management:** Set monthly budgets by category or overall spending, with automatic threshold warnings when you get close to your limits.
* **Web Dashboard:** Launch a lightweight Flask-based local web UI to view interactive charts, categorical breakdowns, and spending trends.
* **Local First:** All your financial data is kept completely private and persisted locally using an efficient SQLite database.
* **Flexible Data Portability:** Easily export your expense history to `CSV` or `JSON`, and import existing records from CSV files.
* **Visual Reports:** Generate quick summaries and ascii-based trend graphs directly in the terminal, or view detailed analytics in the dashboard.

## 🛠️ Built With
* **Python 3.10+** - Core language
* **Click** - Command Line Interface creation
* **Rich** - Beautiful terminal formatting
* **Flask** - Local web dashboard server
* **Plotext** - Terminal plotting
* **SQLite** - Local data storage
