"""Interactive demo: score an applicant, explain the decision, explore the cutoff."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src import scorecard as sc

CUTOFF = 530
st.set_page_config(page_title="Credit Risk Scorecard", layout="wide")


@st.cache_data
def load():
    """Load the test set and score everyone once (cached, so it only runs on first load)."""
    df = pd.read_parquet(ROOT / "data" / "processed" / "test.parquet").set_index("SK_ID_CURR")
    df["score"] = sc.score(df)
    return df


df = load()
st.title("Credit Risk Scorecard")
st.caption(f"Test set: {len(df):,} applicants the model never saw during training")

tab1, tab2 = st.tabs(["Score an applicant", "Choose a cutoff"])

# ---------------- Tab 1: one applicant ----------------
with tab1:
    st.session_state.setdefault("app_id", int(df.index[0]))
    if st.button("🎲 Random applicant"):
        st.session_state.app_id = int(df.sample(1).index[0])
    app_id = st.number_input("Applicant ID (SK_ID_CURR)", step=1, key="app_id")

    if app_id not in df.index:
        st.error("That ID is not in the test set.")
        st.stop()

    person = df.loc[[app_id]]
    s = float(person["score"].iloc[0])
    p = float(sc.prob_default(s))
    approved = s >= CUTOFF

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score", f"{s:.0f}")
    c2.metric("Default risk", f"{p:.1%}")
    c3.metric("Decision", "✅ APPROVE" if approved else "❌ DECLINE")
    c4.metric("What really happened", "Repaid" if person["TARGET"].iloc[0] == 0 else "Defaulted")

    if not approved:
        st.subheader("Reasons for decline")
        for i, r in enumerate(sc.reason_codes(person).iloc[0], 1):
            st.write(f"{i}. {r}")

    st.subheader("Points breakdown")
    pts = sc.points(person).iloc[0]
    table = pd.DataFrame({
        "applicant's value": person[sc.FEATURES].iloc[0].astype(str),
        "points": pts.round(0),
        "vs neutral": (pts - sc.BASE).round(0),
    }).sort_values("vs neutral")
    st.dataframe(table, use_container_width=True)
    st.caption(f"Neutral = {sc.BASE:.0f} points per feature. Negative = pulled the score down.")

# ---------------- Tab 2: the cutoff trade-off ----------------
with tab2:
    cut = st.slider("Cutoff score", 480, 640, CUTOFF, step=5)
    loss = st.slider("A bad loan loses … × what a good loan earns", 1, 20, 5)

    y, ok = df["TARGET"], df["score"] >= cut
    profit = ((ok & (y == 0)).sum() - loss * (ok & (y == 1)).sum())
    approve_all = (y == 0).sum() - loss * (y == 1).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Approved", f"{ok.mean():.1%}")
    c2.metric("Default rate of approved", f"{y[ok].mean():.1%}")
    c3.metric("Defaulters avoided", f"{(~ok & (y == 1)).sum() / (y == 1).sum():.1%}")
    c4.metric("Profit vs approve-all", f"{profit - approve_all:+,}")

    cuts = range(480, 645, 5)
    curve = pd.Series([((df["score"] >= c) & (y == 0)).sum() - loss * ((df["score"] >= c) & (y == 1)).sum()
                       for c in cuts], index=cuts, name="profit")
    st.subheader("Profit at every cutoff")
    st.line_chart(curve)
    st.caption(f"Best cutoff for a {loss}:1 loss ratio: {curve.idxmax()}")
