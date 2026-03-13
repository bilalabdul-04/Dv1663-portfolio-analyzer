"""
Main Flask Application for the Portfolio Analyzer.
Coordinates routing, database interactions, and template rendering.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db, sp_portfolio_summary, fn_asset_return

app = Flask(__name__)
app.secret_key = 'portfolio-analyzer-secret-key-2025'


# ----------------------------------------------------------
# HELPER: Make sure database exists when app starts
# ----------------------------------------------------------
@app.before_request
def before_request():
    """Ensure the database is initialized before any request."""
    import os
    from database import DATABASE
    if not os.path.exists(DATABASE):
        init_db()


# ----------------------------------------------------------
# ROUTE: Dashboard (Home Page)
# ----------------------------------------------------------
@app.route('/')
def index():
    """
    Show the main dashboard with quick stats.
    This is the first page users see.
    """
    conn = get_db()

    # Get all users for the user selector
    users = conn.execute("SELECT * FROM Users").fetchall()

    # Get general stats
    total_assets = conn.execute("SELECT COUNT(*) as count FROM Assets").fetchone()['count']
    total_transactions = conn.execute("SELECT COUNT(*) as count FROM Transactions").fetchone()['count']
    total_users = conn.execute("SELECT COUNT(*) as count FROM Users").fetchone()['count']

    conn.close()
    return render_template('index.html',
                           users=users,
                           total_assets=total_assets,
                           total_transactions=total_transactions,
                           total_users=total_users)


# ----------------------------------------------------------
# ROUTE: Assets Page
# ----------------------------------------------------------
@app.route('/assets')
def assets():
    """List all available assets with their sectors."""
    conn = get_db()
    # JOIN Assets with Sectors to show sector name
    assets_list = conn.execute("""
        SELECT a.asset_id, a.symbol, a.name, a.asset_type, s.sector_name
        FROM Assets a
        JOIN Sectors s ON a.sector_id = s.sector_id
        ORDER BY a.symbol
    """).fetchall()

    sectors = conn.execute("SELECT * FROM Sectors ORDER BY sector_name").fetchall()
    conn.close()
    return render_template('assets.html', assets=assets_list, sectors=sectors)


@app.route('/assets/add', methods=['POST'])
def add_asset():
    """Add a new asset to the database."""
    symbol = request.form['symbol'].upper().strip()
    name = request.form['name'].strip()
    asset_type = request.form['asset_type']
    sector_id = request.form['sector_id']

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO Assets (symbol, name, asset_type, sector_id)
            VALUES (?, ?, ?, ?)
        """, (symbol, name, asset_type, int(sector_id)))
        conn.commit()
        flash(f'Asset {symbol} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding asset: {e}', 'error')
    finally:
        conn.close()

    return redirect(url_for('assets'))


# ----------------------------------------------------------
# ROUTE: Transactions Page
# ----------------------------------------------------------
@app.route('/transactions')
@app.route('/transactions/<int:user_id>')
def transactions(user_id=None):
    """Show transaction history for a user."""
    conn = get_db()
    users = conn.execute("SELECT * FROM Users").fetchall()

    if user_id is None and users:
        user_id = users[0]['user_id']

    transactions_list = []
    if user_id:
        # Fetch transactions with asset and sector details
        transactions_list = conn.execute("""
            SELECT
                t.transaction_id,
                t.transaction_date,
                t.type,
                a.symbol,
                a.name AS asset_name,
                s.sector_name,
                t.quantity,
                t.price_per_unit,
                t.total_amount
            FROM Transactions t
            JOIN Assets a ON t.asset_id = a.asset_id
            JOIN Sectors s ON a.sector_id = s.sector_id
            WHERE t.user_id = ?
            ORDER BY t.transaction_date DESC
        """, (user_id,)).fetchall()

    assets_list = conn.execute("SELECT * FROM Assets ORDER BY symbol").fetchall()
    conn.close()
    return render_template('transactions.html',
                           users=users,
                           current_user_id=user_id,
                           transactions=transactions_list,
                           assets=assets_list)


@app.route('/transactions/add', methods=['POST'])
def add_transaction():
    """Record a new buy or sell transaction."""
    user_id = int(request.form['user_id'])
    asset_id = int(request.form['asset_id'])
    trans_type = request.form['type']
    quantity = float(request.form['quantity'])
    price_per_unit = float(request.form['price_per_unit'])

    conn = get_db()
    try:
        # total_amount is NULL — the trigger calculates it!
        conn.execute("""
            INSERT INTO Transactions (user_id, asset_id, type, quantity, price_per_unit, total_amount)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (user_id, asset_id, trans_type, quantity, price_per_unit))
        conn.commit()
        flash(f'{trans_type} transaction recorded successfully!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        conn.close()

    return redirect(url_for('transactions', user_id=user_id))


# ----------------------------------------------------------
# ROUTE: Portfolio Summary Page
# ----------------------------------------------------------
@app.route('/portfolio')
@app.route('/portfolio/<int:user_id>')
def portfolio(user_id=None):
    """Show complete portfolio summary for a user."""
    conn = get_db()
    users = conn.execute("SELECT * FROM Users").fetchall()
    conn.close()

    if user_id is None and users:
        user_id = users[0]['user_id']

    holdings = []
    totals = {'invested': 0, 'current': 0, 'profit_loss': 0}

    if user_id:
        holdings = sp_portfolio_summary(user_id)
        totals['invested'] = sum(h['invested_amount'] for h in holdings)
        totals['current'] = sum(h['current_value'] for h in holdings)
        totals['profit_loss'] = totals['current'] - totals['invested']

    return render_template('portfolio.html',
                           users=users,
                           current_user_id=user_id,
                           holdings=holdings,
                           totals=totals)


# ----------------------------------------------------------
# ROUTE: Sector Allocation Page
# ----------------------------------------------------------
@app.route('/allocation')
@app.route('/allocation/<int:user_id>')
def allocation(user_id=None):
    """Show portfolio allocation by sector."""
    conn = get_db()
    users = conn.execute("SELECT * FROM Users").fetchall()

    if user_id is None and users:
        user_id = users[0]['user_id']

    allocation_data = []
    if user_id:
        # Calculate sector allocation percentages
        allocation_data = conn.execute("""
            SELECT
                s.sector_name,
                SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END)
                    AS sector_investment,
                ROUND(
                    SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END) * 100.0 /
                    (SELECT SUM(CASE WHEN t2.type = 'BUY' THEN t2.total_amount ELSE -t2.total_amount END)
                     FROM Transactions t2
                     WHERE t2.user_id = ?),
                    2
                ) AS percentage
            FROM Transactions t
            JOIN Assets a ON t.asset_id = a.asset_id
            JOIN Sectors s ON a.sector_id = s.sector_id
            WHERE t.user_id = ?
            GROUP BY s.sector_name
            ORDER BY sector_investment DESC
        """, (user_id, user_id)).fetchall()

    conn.close()
    return render_template('allocation.html',
                           users=users,
                           current_user_id=user_id,
                           allocation=allocation_data)


# ----------------------------------------------------------
# ROUTE: Top Performing Assets Page
# ----------------------------------------------------------
@app.route('/performance')
@app.route('/performance/<int:user_id>')
def performance(user_id=None):
    """Show top performing assets by return percentage."""
    conn = get_db()
    users = conn.execute("SELECT * FROM Users").fetchall()

    if user_id is None and users:
        user_id = users[0]['user_id']

    performance_data = []
    if user_id:
        # QUERY 3 — Top performers
        performance_data = conn.execute("""
            SELECT
                a.symbol,
                a.name,
                a.asset_type,
                ROUND(AVG(t.price_per_unit), 2) AS avg_buy_price,
                (SELECT ph.close_price
                 FROM PriceHistory ph
                 WHERE ph.asset_id = a.asset_id
                 ORDER BY ph.price_date DESC
                 LIMIT 1
                ) AS current_price,
                ROUND(
                    ((SELECT ph.close_price
                      FROM PriceHistory ph
                      WHERE ph.asset_id = a.asset_id
                      ORDER BY ph.price_date DESC
                      LIMIT 1
                    ) - AVG(t.price_per_unit)) / AVG(t.price_per_unit) * 100,
                    2
                ) AS return_pct
            FROM Assets a
            JOIN Transactions t ON a.asset_id = t.asset_id
            WHERE t.type = 'BUY' AND t.user_id = ?
            GROUP BY a.asset_id, a.symbol, a.name, a.asset_type
            ORDER BY return_pct DESC
        """, (user_id,)).fetchall()

    conn.close()
    return render_template('performance.html',
                           users=users,
                           current_user_id=user_id,
                           performance=performance_data)


# ----------------------------------------------------------
# ROUTE: Monthly Trend Page
# ----------------------------------------------------------
@app.route('/trends')
@app.route('/trends/<int:user_id>')
def trends(user_id=None):
    """Show monthly investment trends."""
    conn = get_db()
    users = conn.execute("SELECT * FROM Users").fetchall()

    if user_id is None and users:
        user_id = users[0]['user_id']

    trend_data = []
    if user_id:
        # QUERY 5 — Monthly trend
        trend_data = conn.execute("""
            SELECT
                strftime('%Y-%m', t.transaction_date) AS month,
                COUNT(*) AS num_transactions,
                SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE 0 END)  AS total_bought,
                SUM(CASE WHEN t.type = 'SELL' THEN t.total_amount ELSE 0 END) AS total_sold,
                SUM(CASE WHEN t.type = 'BUY' THEN t.total_amount ELSE -t.total_amount END)
                    AS net_investment
            FROM Transactions t
            WHERE t.user_id = ?
            GROUP BY strftime('%Y-%m', t.transaction_date)
            ORDER BY month
        """, (user_id,)).fetchall()

    conn.close()
    return render_template('trends.html',
                           users=users,
                           current_user_id=user_id,
                           trends=trend_data)


# ----------------------------------------------------------
# Run the app
# ----------------------------------------------------------
if __name__ == '__main__':
    print(" Starting Portfolio Analyzer...")
    print("   Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
