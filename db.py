"""
Persistencia en SQLite: histórico de precios + control de alertas ya enviadas.
"""
import sqlite3
import statistics
from contextlib import contextmanager
from datetime import datetime

from . import config


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with _conn() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                price REAL NOT NULL,
                airline TEXT,
                depart_date TEXT,
                return_date TEXT,
                one_way INTEGER,
                seen_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_route ON prices(origin, destination);

            -- Para no spamear la misma ganga dos veces
            CREATE TABLE IF NOT EXISTS sent_alerts (
                fingerprint TEXT PRIMARY KEY,
                sent_at TEXT NOT NULL
            );
            """
        )


def record_price(origin, destination, price, airline, depart_date, return_date, one_way):
    with _conn() as con:
        con.execute(
            """INSERT INTO prices
               (origin, destination, price, airline, depart_date, return_date, one_way, seen_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (origin, destination, float(price), airline, depart_date, return_date,
             int(one_way), datetime.utcnow().isoformat()),
        )


def median_price(origin, destination):
    """Mediana histórica de la ruta. None si no hay muestras suficientes."""
    with _conn() as con:
        rows = con.execute(
            "SELECT price FROM prices WHERE origin=? AND destination=?",
            (origin, destination),
        ).fetchall()
    vals = [r["price"] for r in rows]
    if len(vals) < config.MIN_SAMPLES:
        return None
    return statistics.median(vals)


def already_sent(fingerprint):
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM sent_alerts WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
    return row is not None


def mark_sent(fingerprint):
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO sent_alerts (fingerprint, sent_at) VALUES (?,?)",
            (fingerprint, datetime.utcnow().isoformat()),
        )
