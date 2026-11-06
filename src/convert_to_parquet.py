"""Convert raw Kaggle CSVs to Parquet using DuckDB."""
from pathlib import Path
import time

import duckdb

RAW = Path("data/raw")
OUT = Path("data/parquet")

# Only the tables our report uses
TABLES = [
    "application_train",
    "application_test",
    "bureau",
    "bureau_balance",
    "previous_application",
    "installments_payments",
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()                     # in-memory database
    con.execute("SET memory_limit = '2GB'")    # protect our 3.8 GB machine

    for name in TABLES:
        src = RAW / f"{name}.csv"
        dst = OUT / f"{name}.parquet"
        start = time.time()

        con.execute(f"""
            COPY (SELECT * FROM read_csv_auto('{src}', sample_size = -1))
            TO '{dst}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)

        rows = con.execute(f"SELECT COUNT(*) FROM '{dst}'").fetchone()[0]
        csv_mb = src.stat().st_size / 1e6
        pq_mb = dst.stat().st_size / 1e6
        print(f"{name:24s} {rows:>12,} rows | "
              f"CSV {csv_mb:7.1f} MB -> Parquet {pq_mb:6.1f} MB | "
              f"{time.time() - start:5.1f}s")


if __name__ == "__main__":
    main()
