# Credit Risk Scorecard

An end-to-end **credit scorecard** built on the [Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) data (307,511 loan applicants, 8.07% default rate): SQL feature engineering, WoE/IV binning, a points-based logistic regression scorecard, a LightGBM challenger with SHAP, validation and stability monitoring, a profit-based cutoff with reason codes, and customer segmentation.

## Results at a glance

| | Result |
|---|---|
| **Scorecard** | 13 features, 129 bins, scaled so **600 points = 50:1 odds**, **+20 points = double the odds** |
| **Test Gini / KS** | **0.498 / 0.375** (train Gini 0.511, so it generalises) |
| **Calibration** | predicted vs actual default rate within ~0.5 pp in every test decile |
| **Risk ranking** | riskiest 30% of applicants hold **64.4%** of all defaults |
| **Challenger** | LightGBM test Gini **0.543**: the scorecard gives up only 0.045 Gini for full explainability |
| **Stability** | score PSI **0.0015** on unseen applicants (stable) |
| **Cutoff** | score **530**: approves 90.6%, avoids 30.9% of defaults, **+10.8% profit** vs approving everyone |

## How it works

**1. Data and SQL features (DuckDB).** Six raw tables (about 45 million rows) are converted to Parquet and joined with SQL to one row per applicant. Engineered features include debt-to-credit ratio at other lenders, share of late instalments in the last 12 months, previous refusal rate and loan-to-goods ratio. 10 of the top 20 features by IV were built in SQL from the bureau, previous-application and instalment tables.


**2. WoE binning and IV (optbinning).** Every feature is binned with a monotonic trend; missing values get their own bin. Selection: IV ≥ 0.02 (105 → 45), drop the weaker of any pair with WoE correlation > 0.7 (→ 33), exclude **gender and family status** for fair-lending reasons, keep the top 16, then backward elimination for wrong signs and p > 0.05 (→ **13**).

**3. Scorecard (statsmodels).** Logistic regression on WoE values, with no class weighting so that probabilities stay calibrated. Coefficients are converted to points per bin (Factor = 20/ln2, Offset = 487.1).

**4. Challenger (LightGBM + SHAP).** Trained on all 105 raw features with 5-fold CV and early stopping. SHAP shows that 12 of its top 20 features are also in the scorecard, so both methods found the same drivers. LightGBM ranked gender as its #9 feature; removing protected features cost only 0.003 Gini because other features act as **proxies**.

**5. Validation and monitoring.** Gini, KS, decile calibration on a held-out 30% test set; PSI and CSI against 48,744 unseen Kaggle test applicants. CSI flagged EXT_SOURCE_1 (0.065), traced to a missingness shift (56.3% → 42.1% missing).

**6. Cutoff and reason codes.** Profit model with a good loan earning 1 unit and a bad loan losing 5 (an assumption). Break-even PD = 1/6, so the theoretical cutoff is 534; the empirical optimum is **530**. A cutoff of 600 would approve only 13.4% of applicants and earn 79% less. Reason codes list the features that pulled an applicant **below the neutral score**, with the three external scores grouped as one reason.

**7. Segmentation (K-means, K = 4)** on age, income, credit/income, annuity/income, years employed and active loans:

| Segment | Share | Default rate | Scorecard Gini |
|---|---|---|---|
| Pensioners & older customers | 26% | 6.4% | 0.48 |
| Established professionals | 13% | 5.2% | 0.52 |
| Young early-career | 41% | 9.9% | 0.50 |
| Stretched borrowers (loan ≈ 7× income) | 20% | 8.4% | 0.50 |

The scorecard ranks equally well within every segment. Life stage matters more than loan size: young early-career applicants default more than heavily borrowed ones.

## Limitations

- **No out-of-time test**: the data has no application dates, so validation is out-of-sample, not out-of-time.
- **Proxy variables**: protected features were removed, but outcome-based fairness testing (approval rates by group) is a next step.
- **Profit ratio is an assumption**: the 5:1 loss/gain ratio should come from the bank's real loss data.
- **Segments overlap**: silhouette ≈ 0.2, so the segments are useful business summaries rather than sharply separated groups.
- The three EXT_SOURCE features are opaque third-party scores and dominate the model.

## Project structure

```text
sql/          feature engineering queries (run in order)
src/          convert_to_parquet.py, build_features.py, split_data.py, scorecard.py
notebooks/    01_eda → 03_woe_binning → 04_scorecard → 05_lightgbm → 06_validation
              → 07_cutoff_reasons → 08_segmentation
models/       selected_features.json, lr_model.json, scorecard.csv (the 129-row scorecard)
```

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# needs a Kaggle API token and accepting the competition rules
kaggle competitions download -c home-credit-default-risk -p data/raw
unzip data/raw/home-credit-default-risk.zip -d data/raw

python src/convert_to_parquet.py
python src/build_features.py
python src/split_data.py
jupyter lab        # then run the notebooks in order
```

Tested on WSL2 Ubuntu with 5 GB RAM; DuckDB keeps memory use low.


