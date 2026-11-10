"""Build the applicant-level feature table by running the SQL files in sql/ in order."""
import os
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
OUT = ROOT / "data" / "processed" / "features.parquet"

MAX_MISSING_PCT = 50
KEEP_DESPITE_MISSING = {"EXT_SOURCE_1"}   # strong predictor, see EDA notebook


def columns_to_drop(con):
    """Application columns with more than 50% missing values, except the ones we keep."""
    rows = con.execute("""
        SELECT column_name, null_percentage
        FROM (SUMMARIZE SELECT * FROM 'data/parquet/application_train.parquet')
    """).fetchall()
    return [name for name, pct in rows
            if pct > MAX_MISSING_PCT and name not in KEEP_DESPITE_MISSING]


def main():
    os.chdir(ROOT)                          # so 'data/...' paths in the SQL work
    con = duckdb.connect()
    con.execute("SET memory_limit = '2GB'")

    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        table = sql_file.stem.split("_", 1)[1]      # '02_bureau_agg' -> 'bureau_agg'
        start = time.time()
        con.execute(sql_file.read_text())

        rows, ids = con.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT SK_ID_CURR) FROM {table}"
        ).fetchall()[0]
        status = "OK" if rows == ids else "DUPLICATES!"
        print(f"{sql_file.name:20s} -> {table:11s} {rows:>9,} rows "
              f"{ids:>9,} applicants  {status}  ({time.time() - start:.1f}s)")

    if (SQL_DIR / "05_features.sql").exists():
        drop = columns_to_drop(con)
        print(f"Dropping {len(drop)} application columns with > {MAX_MISSING_PCT}% missing")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        con.execute(f"""
            COPY (SELECT * EXCLUDE ({', '.join(drop)}) FROM features)
            TO '{OUT}' (FORMAT PARQUET)
        """)
        n_cols = len(con.execute(f"DESCRIBE SELECT * FROM '{OUT}'").fetchall())
        print(f"Saved {OUT.relative_to(ROOT)} with {n_cols} columns")


if __name__ == "__main__":
    main()
