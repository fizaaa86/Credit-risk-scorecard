"""Load the saved scorecard once and score applicants. Imported by the notebooks."""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"

with open(MODELS / "binning_process.pkl", "rb") as f:
    BP = pickle.load(f)
with open(MODELS / "lr_model.json") as f:
    _lr = json.load(f)

FEATURES = _lr["features"]
INTERCEPT = _lr["params"]["const"]
COEFS = pd.Series(_lr["params"]).drop("const")[FEATURES]
FACTOR, OFFSET = _lr["factor"], _lr["offset"]
ALL_FEATURES = list(BP.variable_names)


def woe(df):
    """WoE value of each scorecard feature, for each applicant."""
    w = BP.transform(df[ALL_FEATURES], metric="woe",
                     metric_missing="empirical", metric_special="empirical")
    return pd.DataFrame(np.asarray(w), columns=ALL_FEATURES, index=df.index)[FEATURES]


def points(df):
    """Points per feature (rows = applicants, columns = the 13 features)."""
    base = (OFFSET - FACTOR * INTERCEPT) / len(FEATURES)
    return -FACTOR * woe(df) * COEFS + base


def score(df):
    """Total score = sum of the 13 feature points."""
    return points(df).sum(axis=1)


def prob_default(scores):
    """Turn a score back into a probability of default."""
    logit = (OFFSET - scores) / FACTOR
    return 1 / (1 + np.exp(-logit))



REASONS = {
    "EXT_SOURCE_1": "External credit score (source 1) is low",
    "EXT_SOURCE_2": "External credit score (source 2) is low",
    "EXT_SOURCE_3": "External credit score (source 3) is low",
    "YEARS_EMPLOYED": "Short time in current employment",
    "BUREAU_DEBT_TO_CREDIT": "High outstanding debt relative to credit with other lenders",
    "INST_LATE_SHARE_LAST12": "Late instalment payments in the last 12 months",
    "BUREAU_YEARS_SINCE_FIRST": "Length of credit history",
    "OCCUPATION_TYPE": "Occupation type",
    "ORGANIZATION_TYPE": "Employer type",
    "AMT_CREDIT_TO_GOODS_RATIO": "Loan amount high relative to the price of the goods",
    "PREV_REFUSAL_RATE": "Previous loan applications were refused",
    "BUREAU_ACTIVE_COUNT": "Number of active loans with other lenders",
    "PREV_GRANTED_TO_REQUESTED": "Previous loans: amount granted vs requested",
}


BASE = (OFFSET - FACTOR * INTERCEPT) / len(FEATURES)     # neutral points per feature (≈43)

GROUPS = {f: f for f in FEATURES}
GROUPS.update({"EXT_SOURCE_1": "EXT_SOURCES", "EXT_SOURCE_2": "EXT_SOURCES", "EXT_SOURCE_3": "EXT_SOURCES"})
REASONS["EXT_SOURCES"] = "Low external credit scores"


def reason_codes(df, n=3):
    """Top-n reasons per applicant: what pulled their score BELOW average the most."""
    below = BASE - points(df)                   # > 0 means this feature pulled the score down
    below = below.T.groupby(GROUPS).sum().T     # add the 3 external scores together as one reason
    return below.apply(lambda row: [REASONS[f] for f in row[row > 0].nlargest(n).index], axis=1)
