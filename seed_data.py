"""
seed_data.py — Populate the Database with Sample Data
======================================================
BEGINNER GUIDE:
- Run this script AFTER database.py to fill the database
  with realistic sample data for testing and demonstration.
- It creates users, sectors, assets, transactions, and price history.

HOW TO RUN:
    python seed_data.py
"""

from database import get_db, init_db


def seed():
    """Insert sample data into all tables."""

    # Step 1: Initialize the database (create tables if needed)
    init_db()

    conn = get_db()
    cursor = conn.cursor()

    # ----------------------------------------------------------
    # USERS — Two sample investors
    # ----------------------------------------------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO Users (username, email, password) VALUES (?, ?, ?)
    """, [
        ('alice', 'alice@example.com', 'password123'),
        ('bob', 'bob@example.com', 'password456'),
    ])

    # ----------------------------------------------------------
    # SECTORS — Five industry categories
    # ----------------------------------------------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO Sectors (sector_name) VALUES (?)
    """, [
        ('Technology',),
        ('Healthcare',),
        ('Finance',),
        ('Energy',),
        ('Consumer Goods',),
    ])

    # ----------------------------------------------------------
    # ASSETS — 10 financial instruments across sectors
    # ----------------------------------------------------------
    # (symbol, name, asset_type, sector_id)
    cursor.executemany("""
        INSERT OR IGNORE INTO Assets (symbol, name, asset_type, sector_id) VALUES (?, ?, ?, ?)
    """, [
        ('AAPL', 'Apple Inc.',               'Stock',  1),  # Technology
        ('MSFT', 'Microsoft Corp.',           'Stock',  1),  # Technology
        ('GOOGL', 'Alphabet Inc.',            'Stock',  1),  # Technology
        ('JNJ',  'Johnson & Johnson',         'Stock',  2),  # Healthcare
        ('PFE',  'Pfizer Inc.',               'Stock',  2),  # Healthcare
        ('JPM',  'JPMorgan Chase & Co.',      'Stock',  3),  # Finance
        ('V',    'Visa Inc.',                 'Stock',  3),  # Finance
        ('XOM',  'Exxon Mobil Corp.',         'Stock',  4),  # Energy
        ('BTC',  'Bitcoin',                   'Crypto', 1),  # Technology (crypto)
        ('VTI',  'Vanguard Total Stock ETF',  'ETF',    5),  # Consumer Goods
    ])

    # ----------------------------------------------------------
    # TRANSACTIONS — 25 buy/sell transactions
    # ----------------------------------------------------------
    # (user_id, asset_id, type, quantity, price_per_unit, total_amount, transaction_date)
    # NOTE: total_amount is set to NULL so the trigger calculates it!
    cursor.executemany("""
        INSERT INTO Transactions (user_id, asset_id, type, quantity, price_per_unit, total_amount, transaction_date)
        VALUES (?, ?, ?, ?, ?, NULL, ?)
    """, [
        # Alice's transactions
        (1, 1, 'BUY',  10,  150.00, '2025-01-15'),  # Buy 10 AAPL
        (1, 2, 'BUY',  5,   380.00, '2025-01-20'),  # Buy 5 MSFT
        (1, 3, 'BUY',  3,   140.00, '2025-02-01'),  # Buy 3 GOOGL
        (1, 4, 'BUY',  15,  155.00, '2025-02-10'),  # Buy 15 JNJ
        (1, 6, 'BUY',  8,   195.00, '2025-02-15'),  # Buy 8 JPM
        (1, 8, 'BUY',  20,  105.00, '2025-03-01'),  # Buy 20 XOM
        (1, 9, 'BUY',  0.5, 42000.00, '2025-03-05'), # Buy 0.5 BTC
        (1, 10, 'BUY', 25,  240.00, '2025-03-10'),  # Buy 25 VTI
        (1, 1, 'BUY',  5,   155.00, '2025-04-01'),  # Buy 5 more AAPL
        (1, 1, 'SELL', 3,   165.00, '2025-05-01'),  # Sell 3 AAPL
        (1, 2, 'SELL', 2,   400.00, '2025-05-15'),  # Sell 2 MSFT
        (1, 5, 'BUY',  30,  28.50,  '2025-06-01'),  # Buy 30 PFE
        (1, 7, 'BUY',  10,  275.00, '2025-06-15'),  # Buy 10 Visa

        # Bob's transactions
        (2, 1, 'BUY',  20,  148.00, '2025-01-10'),  # Buy 20 AAPL
        (2, 3, 'BUY',  8,   135.00, '2025-01-25'),  # Buy 8 GOOGL
        (2, 5, 'BUY',  50,  27.00,  '2025-02-05'),  # Buy 50 PFE
        (2, 7, 'BUY',  12,  270.00, '2025-02-20'),  # Buy 12 Visa
        (2, 8, 'BUY',  30,  102.00, '2025-03-01'),  # Buy 30 XOM
        (2, 9, 'BUY',  1.0, 41000.00, '2025-03-10'), # Buy 1 BTC
        (2, 10, 'BUY', 40,  238.00, '2025-03-15'),  # Buy 40 VTI
        (2, 1, 'SELL', 5,   160.00, '2025-04-15'),  # Sell 5 AAPL
        (2, 5, 'SELL', 10,  30.00,  '2025-05-01'),  # Sell 10 PFE
        (2, 6, 'BUY',  15,  198.00, '2025-05-20'),  # Buy 15 JPM
        (2, 4, 'BUY',  10,  158.00, '2025-06-01'),  # Buy 10 JNJ
        (2, 2, 'BUY',  7,   390.00, '2025-06-10'),  # Buy 7 MSFT
    ])

    # ----------------------------------------------------------
    # PRICE HISTORY — Historical prices for all assets
    # ----------------------------------------------------------
    # These simulate price movements over several months.
    # The LATEST date's price is used as the "current" price.
    cursor.executemany("""
        INSERT OR IGNORE INTO PriceHistory (asset_id, price_date, close_price) VALUES (?, ?, ?)
    """, [
        # AAPL prices
        (1, '2025-01-01', 148.00), (1, '2025-02-01', 152.00),
        (1, '2025-03-01', 158.00), (1, '2025-04-01', 162.00),
        (1, '2025-05-01', 165.00), (1, '2025-06-01', 170.00),
        (1, '2025-07-01', 175.00),

        # MSFT prices
        (2, '2025-01-01', 375.00), (2, '2025-02-01', 382.00),
        (2, '2025-03-01', 390.00), (2, '2025-04-01', 395.00),
        (2, '2025-05-01', 400.00), (2, '2025-06-01', 410.00),
        (2, '2025-07-01', 420.00),

        # GOOGL prices
        (3, '2025-01-01', 133.00), (3, '2025-02-01', 138.00),
        (3, '2025-03-01', 142.00), (3, '2025-04-01', 148.00),
        (3, '2025-05-01', 152.00), (3, '2025-06-01', 155.00),
        (3, '2025-07-01', 160.00),

        # JNJ prices
        (4, '2025-01-01', 153.00), (4, '2025-02-01', 156.00),
        (4, '2025-03-01', 158.00), (4, '2025-04-01', 160.00),
        (4, '2025-05-01', 162.00), (4, '2025-06-01', 165.00),
        (4, '2025-07-01', 163.00),

        # PFE prices
        (5, '2025-01-01', 26.50), (5, '2025-02-01', 27.50),
        (5, '2025-03-01', 28.00), (5, '2025-04-01', 29.00),
        (5, '2025-05-01', 30.00), (5, '2025-06-01', 31.00),
        (5, '2025-07-01', 32.00),

        # JPM prices
        (6, '2025-01-01', 192.00), (6, '2025-02-01', 196.00),
        (6, '2025-03-01', 200.00), (6, '2025-04-01', 205.00),
        (6, '2025-05-01', 210.00), (6, '2025-06-01', 215.00),
        (6, '2025-07-01', 220.00),

        # V (Visa) prices
        (7, '2025-01-01', 268.00), (7, '2025-02-01', 272.00),
        (7, '2025-03-01', 278.00), (7, '2025-04-01', 282.00),
        (7, '2025-05-01', 285.00), (7, '2025-06-01', 290.00),
        (7, '2025-07-01', 295.00),

        # XOM prices
        (8, '2025-01-01', 100.00), (8, '2025-02-01', 103.00),
        (8, '2025-03-01', 106.00), (8, '2025-04-01', 108.00),
        (8, '2025-05-01', 110.00), (8, '2025-06-01', 112.00),
        (8, '2025-07-01', 115.00),

        # BTC prices
        (9, '2025-01-01', 40000.00), (9, '2025-02-01', 42000.00),
        (9, '2025-03-01', 45000.00), (9, '2025-04-01', 47000.00),
        (9, '2025-05-01', 50000.00), (9, '2025-06-01', 52000.00),
        (9, '2025-07-01', 55000.00),

        # VTI (ETF) prices
        (10, '2025-01-01', 235.00), (10, '2025-02-01', 238.00),
        (10, '2025-03-01', 242.00), (10, '2025-04-01', 245.00),
        (10, '2025-05-01', 248.00), (10, '2025-06-01', 252.00),
        (10, '2025-07-01', 258.00),
    ])

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully!")
    print("   - 2 users")
    print("   - 5 sectors")
    print("   - 10 assets")
    print("   - 25 transactions")
    print("   - 70 price history records")


if __name__ == '__main__':
    seed()
