"""
database.py — Database Connection & Initialization
====================================================
BEGINNER GUIDE:
- This file handles connecting to the SQLite database.
- It reads schema.sql and creates all the tables.
- Other files import 'get_db()' to get a database connection.

WHAT IS SQLite?
- SQLite is a lightweight database stored in a single file.
- Python has built-in support for it — no installation needed!
- The database file will be called 'portfolio.db'.
"""

import sqlite3
import os

# Path to the database file (same folder as this script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'portfolio.db')


def get_db():
    """
    Create and return a connection to the SQLite database.

    WHAT IS A CONNECTION?
    Think of it like opening a file — you need to 'connect' to the
    database before you can read or write data.

    row_factory = sqlite3.Row makes query results behave like
    dictionaries, so you can access columns by name (e.g., row['username']).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row          # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key checks
    return conn


def init_db():
    """
    Initialize the database by running schema.sql.

    This creates all tables and triggers if they don't exist yet.
    It only runs the schema — it does NOT insert sample data.
    """
    conn = get_db()
    schema_path = os.path.join(BASE_DIR, 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def close_db(conn):
    """Close the database connection."""
    if conn:
        conn.close()


# ---------- Stored Procedure (simulated) ----------
# WHAT IS A STORED PROCEDURE?
# In bigger databases (MySQL, PostgreSQL), a stored procedure is
# a saved block of SQL code you can call by name. SQLite doesn't
# support them natively, so we implement the same logic in Python
# with raw SQL queries — which is just as valid for this course.

def sp_portfolio_summary(user_id):
    """
    STORED PROCEDURE: Get a complete portfolio summary for a user.

    Returns a list of dictionaries, one per asset the user holds,
    with: symbol, name, quantity_held, avg_buy_price, current_price,
    invested_amount, current_value, profit_loss, return_pct.
    """
    conn = get_db()
    cursor = conn.execute("""
        SELECT
            a.asset_id,
            a.symbol,
            a.name,
            a.asset_type,
            s.sector_name,
            -- Net quantity held (buys - sells)
            COALESCE(SUM(CASE WHEN t.type = 'BUY' THEN t.quantity ELSE -t.quantity END), 0)
                AS quantity_held,
            -- Average price paid per unit on buys
            ROUND(AVG(CASE WHEN t.type = 'BUY' THEN t.price_per_unit END), 2)
                AS avg_buy_price,
            -- Total amount invested (buys - sells)
            COALESCE(SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END), 0)
                AS invested_amount
        FROM Transactions t
        JOIN Assets a ON t.asset_id = a.asset_id
        JOIN Sectors s ON a.sector_id = s.sector_id
        WHERE t.user_id = ?
        GROUP BY a.asset_id, a.symbol, a.name, a.asset_type, s.sector_name
        HAVING quantity_held > 0
    """, (user_id,))

    holdings = []
    for row in cursor.fetchall():
        # Get the latest price for this asset
        price_row = conn.execute("""
            SELECT close_price FROM PriceHistory
            WHERE asset_id = ?
            ORDER BY price_date DESC
            LIMIT 1
        """, (row['asset_id'],)).fetchone()

        current_price = price_row['close_price'] if price_row else row['avg_buy_price']
        current_value = row['quantity_held'] * current_price
        profit_loss = current_value - row['invested_amount']
        return_pct = (profit_loss / row['invested_amount'] * 100) if row['invested_amount'] != 0 else 0

        holdings.append({
            'symbol': row['symbol'],
            'name': row['name'],
            'asset_type': row['asset_type'],
            'sector': row['sector_name'],
            'quantity_held': row['quantity_held'],
            'avg_buy_price': row['avg_buy_price'],
            'current_price': round(current_price, 2),
            'invested_amount': round(row['invested_amount'], 2),
            'current_value': round(current_value, 2),
            'profit_loss': round(profit_loss, 2),
            'return_pct': round(return_pct, 2)
        })

    conn.close()
    return holdings


# ---------- SQL Function (simulated) ----------
def fn_asset_return(user_id, asset_id):
    """
    SQL FUNCTION: Compute the return percentage for a specific asset.

    Formula: ((current_price - avg_buy_price) / avg_buy_price) × 100

    Returns a dictionary with the calculation details.
    """
    conn = get_db()

    # Get average buy price
    buy_row = conn.execute("""
        SELECT AVG(price_per_unit) AS avg_price
        FROM Transactions
        WHERE user_id = ? AND asset_id = ? AND type = 'BUY'
    """, (user_id, asset_id)).fetchone()

    # Get latest market price
    price_row = conn.execute("""
        SELECT close_price
        FROM PriceHistory
        WHERE asset_id = ?
        ORDER BY price_date DESC
        LIMIT 1
    """, (asset_id,)).fetchone()

    conn.close()

    if not buy_row or not buy_row['avg_price'] or not price_row:
        return {'return_pct': 0, 'avg_buy_price': 0, 'current_price': 0}

    avg_price = buy_row['avg_price']
    current_price = price_row['close_price']
    return_pct = ((current_price - avg_price) / avg_price) * 100

    return {
        'avg_buy_price': round(avg_price, 2),
        'current_price': round(current_price, 2),
        'return_pct': round(return_pct, 2)
    }


if __name__ == '__main__':
    # If you run this file directly, it will create/reset the database
    init_db()
