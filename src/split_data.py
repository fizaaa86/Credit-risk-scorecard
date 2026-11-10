"""Split labelled applicants 70/30 into train and test, stratified on TARGET."""
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

TEST_SIZE = 0.30
RANDOM_STATE = 42


def describe(name, df):
    n, bad = len(df), int(df["TARGET"].sum())
    print(f"{name:12s} {n:>8,} applicants  {bad:>7,} defaults  ({bad / n:.2%})")


def main():
    features = pd.read_parquet(PROCESSED / "features.parquet")

    labelled = features[features["IS_KAGGLE_TEST"] == 0].copy()
    labelled["TARGET"] = labelled["TARGET"].astype(int)
    kaggle_test = features[features["IS_KAGGLE_TEST"] == 1]

    train, test = train_test_split(
        labelled,
        test_size=TEST_SIZE,
        stratify=labelled["TARGET"],
        random_state=RANDOM_STATE,
    )

    describe("labelled", labelled)
    describe("train", train)
    describe("test", test)
    print(f"{'kaggle_test':12s} {len(kaggle_test):>8,} applicants  (no labels, PSI only)")

    train.to_parquet(PROCESSED / "train.parquet", index=False)
    test.to_parquet(PROCESSED / "test.parquet", index=False)
    kaggle_test.to_parquet(PROCESSED / "kaggle_test.parquet", index=False)
    print("Saved train.parquet, test.parquet, kaggle_test.parquet")


if __name__ == "__main__":
    main()
