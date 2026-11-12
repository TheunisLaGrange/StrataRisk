import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_VERSION = "1.0"


def export_sqlite_db(results: List[Dict[str, Any]], output_dir: Path) -> str:
    """
    Persists screened equity results to a versioned SQLite database
    (stratarisk_store.db) so the backend and C# GUI can evolve independently.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "stratarisk_store.db"
    run_timestamp = datetime.now().isoformat()

    known_keys = {
        "symbol", "name", "sector", "current_price", "trailing_pe",
        "peg_ratio", "roe_pct", "ema_50", "sma_200", "trend_signal",
        "cash_to_debt", "net_cash", "fcf_yield_pct", "stress_score",
        "risk_tier", "passed_screen", "risk_flags"
    }

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")

        # 1. Schema Metadata Table (Contract Version)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
            ("schema_version", SCHEMA_VERSION),
        )
        cursor.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
            ("last_updated", run_timestamp),
        )

        # 2. Scan Runs Audit Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TEXT NOT NULL,
                record_count INTEGER NOT NULL
            )
        """)
        cursor.execute(
            "INSERT INTO scan_runs (run_timestamp, record_count) VALUES (?, ?)",
            (run_timestamp, len(results)),
        )
        run_id = cursor.lastrowid

        # 3. Screening Results Table (with forward-compatible extra_metrics_json)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT,
                sector TEXT,
                current_price REAL,
                trailing_pe REAL,
                peg_ratio REAL,
                roe_pct REAL,
                ema_50 REAL,
                sma_200 REAL,
                trend_signal TEXT,
                cash_to_debt REAL,
                net_cash REAL,
                fcf_yield_pct REAL,
                stress_score INTEGER,
                risk_tier TEXT,
                passed_screen INTEGER,
                risk_flags TEXT,
                extra_metrics_json TEXT,
                FOREIGN KEY (run_id) REFERENCES scan_runs(run_id)
            )
        """)

        for row in results:
            flags_str = ";".join(row.get("risk_flags", [])) or "NONE"
            extra_metrics = {k: v for k, v in row.items() if k not in known_keys}

            cursor.execute(
                """
                INSERT INTO screening_results (
                    run_id, symbol, name, sector, current_price, trailing_pe,
                    peg_ratio, roe_pct, ema_50, sma_200, trend_signal,
                    cash_to_debt, net_cash, fcf_yield_pct, stress_score,
                    risk_tier, passed_screen, risk_flags, extra_metrics_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row.get("symbol"),
                    row.get("name"),
                    row.get("sector"),
                    row.get("current_price"),
                    row.get("trailing_pe"),
                    row.get("peg_ratio"),
                    row.get("roe_pct"),
                    row.get("ema_50"),
                    row.get("sma_200"),
                    row.get("trend_signal"),
                    row.get("cash_to_debt"),
                    row.get("net_cash"),
                    row.get("fcf_yield_pct"),
                    row.get("stress_score"),
                    row.get("risk_tier"),
                    1 if row.get("passed_screen") else 0,
                    flags_str,
                    json.dumps(extra_metrics) if extra_metrics else "{}",
                ),
            )

        conn.commit()

    return str(db_path)
