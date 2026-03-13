-- ============================================================
-- CLEAR EXISTING DATA (To allow running this script multiple times)
-- ============================================================
DROP TRIGGER IF EXISTS trg_calculate_total;
DROP TRIGGER IF EXISTS trg_prevent_oversell;
DROP INDEX IF EXISTS idx_transactions_user;
DROP INDEX IF EXISTS idx_transactions_asset;
DROP INDEX IF EXISTS idx_pricehistory_asset;
DROP INDEX IF EXISTS idx_assets_sector;
DROP TABLE IF EXISTS PriceHistory;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Assets;
DROP TABLE IF EXISTS Sectors;
DROP TABLE IF EXISTS Users;

-- ============================================================
-- TABLE 1: Users
-- ============================================================
-- Stores people who use the application.
-- Each user can have many transactions (1:N relationship).
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- TABLE 2: Sectors
-- ============================================================
-- Industry categories like Technology, Healthcare, Finance.
-- Each sector can contain many assets (1:N relationship).
CREATE TABLE Sectors (
    sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name TEXT NOT NULL UNIQUE
);

-- ============================================================
-- TABLE 3: Assets
-- ============================================================
-- Financial instruments: stocks, ETFs, or cryptocurrencies.
-- Each asset belongs to exactly one sector (N:1 relationship).
-- Each asset can appear in many transactions (1:N).
CREATE TABLE Assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE, -- e.g. "AAPL", "BTC"
    name TEXT NOT NULL, -- e.g. "Apple Inc."
    asset_type TEXT NOT NULL CHECK (
        asset_type IN ('Stock', 'ETF', 'Crypto')
    ),
    sector_id INTEGER NOT NULL,
    FOREIGN KEY (sector_id) REFERENCES Sectors (sector_id)
);

-- ============================================================
-- TABLE 4: Transactions
-- ============================================================
-- Records every buy or sell a user makes.
-- Links to both Users (who?) and Assets (what?).
-- total_amount is auto-calculated by a trigger (see below).
CREATE TABLE Transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('BUY', 'SELL')),
    quantity REAL NOT NULL CHECK (quantity > 0),
    price_per_unit REAL NOT NULL CHECK (price_per_unit > 0),
    total_amount REAL, -- auto-filled by trigger
    transaction_date TEXT NOT NULL DEFAULT (date('now')),
    FOREIGN KEY (user_id) REFERENCES Users (user_id),
    FOREIGN KEY (asset_id) REFERENCES Assets (asset_id)
);

-- ============================================================
-- TABLE 5: PriceHistory
-- ============================================================
-- Historical closing prices for each asset.
-- Used to calculate current portfolio value.
CREATE TABLE PriceHistory (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    price_date TEXT NOT NULL,
    close_price REAL NOT NULL CHECK (close_price >= 0),
    FOREIGN KEY (asset_id) REFERENCES Assets (asset_id),
    UNIQUE (asset_id, price_date) -- one price per asset per day
);

-- TRIGGER: Calculate total_amount automatically before insertion.
CREATE TRIGGER trg_calculate_total
BEFORE INSERT ON Transactions
FOR EACH ROW
WHEN NEW.total_amount IS NULL
BEGIN
    SELECT RAISE(ABORT, 'trigger placeholder');
END;

-- SQLite doesn't allow modifying NEW values in BEFORE triggers,
-- so we use an AFTER INSERT trigger with UPDATE instead:
DROP TRIGGER IF EXISTS trg_calculate_total;

CREATE TRIGGER trg_calculate_total
AFTER INSERT ON Transactions
FOR EACH ROW
WHEN NEW.total_amount IS NULL
BEGIN
    UPDATE Transactions
    SET total_amount = NEW.quantity * NEW.price_per_unit
    WHERE transaction_id = NEW.transaction_id;
END;

-- TRIGGER: Ensure a user has sufficient quantity of an asset before allowing a SELL transaction.
DROP TRIGGER IF EXISTS trg_prevent_oversell;

CREATE TRIGGER trg_prevent_oversell
BEFORE INSERT ON Transactions
FOR EACH ROW
WHEN NEW.type = 'SELL'
BEGIN
    SELECT CASE
        WHEN (
            COALESCE(
                (SELECT SUM(CASE WHEN type = 'BUY' THEN quantity ELSE -quantity END)
                 FROM Transactions
                 WHERE user_id = NEW.user_id AND asset_id = NEW.asset_id),
                0
            ) < NEW.quantity
        )
        THEN RAISE(ABORT, 'Cannot sell more than you own')
    END;
END;

-- ============================================================
-- INDEX: Speed up common queries
-- ============================================================
DROP INDEX IF EXISTS idx_transactions_user;
CREATE INDEX idx_transactions_user ON Transactions (user_id);

DROP INDEX IF EXISTS idx_transactions_asset;
CREATE INDEX idx_transactions_asset ON Transactions (asset_id);

DROP INDEX IF EXISTS idx_pricehistory_asset;
CREATE INDEX idx_pricehistory_asset ON PriceHistory (asset_id);

DROP INDEX IF EXISTS idx_assets_sector;
CREATE INDEX idx_assets_sector ON Assets (sector_id);