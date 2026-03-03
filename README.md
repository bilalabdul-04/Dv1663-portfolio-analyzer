# 📊 Personal Investment Portfolio Analyzer

A database-driven web application for tracking and analyzing investment portfolios.  
Built with **Python Flask** + **SQLite** using **raw SQL queries** (no ORM).

> **Course:** Databaser DV1663 — Blekinge Tekniska Högskola (BTH)

---

## Features

- 👤 User account management
- 💎 Asset tracking (Stocks, ETFs, Cryptocurrencies)
- 🎯 Sector-based categorization
- 💱 Buy/Sell transaction recording
- 💼 Portfolio summary with profit/loss calculation
- 📊 Sector allocation analysis
- 🏆 Top performing assets ranking
- 📈 Monthly investment trend analysis

## Tech Stack

- **Backend:** Python 3, Flask
- **Database:** SQLite (raw SQL, no ORM)
- **Frontend:** HTML5, CSS3 (Jinja2 templates)

## How to Run

```bash
# 1. Install Flask
pip install flask

# 2. Seed the database with sample data
python seed_data.py

# 3. Start the web server
python app.py

# 4. Open in browser
# http://localhost:5000
```

## Database Design

The system uses 5 related tables:
- **Users** — application users
- **Sectors** — industry categories (Technology, Healthcare, etc.)
- **Assets** — financial instruments (linked to sectors)
- **Transactions** — buy/sell records (linked to users and assets)
- **PriceHistory** — historical prices (linked to assets)

## SQL Features Used

- Multi-table JOINs
- Aggregation (SUM, AVG, COUNT) & GROUP BY
- Triggers (auto-calculate total, prevent overselling)
- Stored Procedure (portfolio summary)
- SQL Function (asset return calculation)
