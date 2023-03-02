PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

ALTER TABLE plans RENAME TO backup_plans;
DROP INDEX plans_for_day_and_territory;

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    day INTEGER NOT NULL,
    territory INTEGER NOT NULL,
    tier INTEGER,
    quota INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);
CREATE UNIQUE INDEX plans_for_day_and_territory ON plans (season, day, territory, tier);

INSERT INTO plans(id, season, day, territory, tier, quota)
SELECT id, season, day, territory, tier, quota FROM backup_plans;

ALTER TABLE orders RENAME TO backup_orders;
DROP INDEX orders_for_day_and_user;

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER,
    day INTEGER,
    user TEXT NOT NULL,
    territory INTEGER NOT NULL,
    stars INTEGER,
    accepted BOOLEAN DEFAULT FALSE,
    uuid TEXT NOT NULL UNIQUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);
CREATE UNIQUE INDEX orders_for_day_and_user ON orders (season, day, user);

INSERT INTO orders (id, season, day, user, territory, stars, accepted, uuid)
SELECT id, season, day, user, territory, stars, accepted, uuid FROM backup_orders;

ALTER TABLE offers RENAME TO backup_offers;
DROP INDEX offer_user_rank;

CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    day INTEGER NOT NULL,
    user TEXT NOT NULL,
    territory INTEGER NOT NULL,
    stars INTEGER NOT NULL,
    rank INTEGER NOT NULL DEFAULT 0,
    uuid TEXT NOT NULL UNIQUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);
CREATE UNIQUE INDEX offer_user_rank ON offers (season, day, user, rank);

INSERT INTO offers (id, season, day, user, territory, stars, rank, uuid)
SELECT id, season, day, user, territory, stars, rank, uuid FROM backup_offers;

UPDATE plans SET timestamp=NULL;
UPDATE orders SET timestamp=NULL;
UPDATE offers SET timestamp=NULL;

DROP TABLE backup_plans;
DROP TABLE backup_orders;
DROP TABLE backup_offers;

COMMIT;

PRAGMA foreign_keys=on;
