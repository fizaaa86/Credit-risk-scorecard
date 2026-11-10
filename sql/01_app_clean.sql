-- One row per applicant: Kaggle train + test, cleaned, with affordability ratios.
CREATE OR REPLACE TABLE app_clean AS
WITH app_all AS (
    SELECT *, 0 AS IS_KAGGLE_TEST FROM 'data/parquet/application_train.parquet'
    UNION ALL BY NAME
    SELECT *, 1 AS IS_KAGGLE_TEST FROM 'data/parquet/application_test.parquet'
)
SELECT
    * EXCLUDE (DAYS_BIRTH, DAYS_EMPLOYED),

    -- Days (negative) -> years (positive)
    -DAYS_BIRTH / 365.25 AS AGE_YEARS,

    -- EDA finding: 365243 is a placeholder for pensioners -> NULL + flag
    CASE WHEN DAYS_EMPLOYED = 365243 THEN NULL
         ELSE -DAYS_EMPLOYED / 365.25 END AS YEARS_EMPLOYED,
    CASE WHEN DAYS_EMPLOYED = 365243 THEN 1 ELSE 0 END AS DAYS_EMPLOYED_ANOM,

    -- Affordability ratios
    AMT_CREDIT       / NULLIF(AMT_INCOME_TOTAL, 0) AS CREDIT_TO_INCOME,
    AMT_ANNUITY      / NULLIF(AMT_INCOME_TOTAL, 0) AS ANNUITY_TO_INCOME,
    AMT_CREDIT       / NULLIF(AMT_GOODS_PRICE, 0)  AS AMT_CREDIT_TO_GOODS_RATIO,
    AMT_INCOME_TOTAL / NULLIF(CNT_FAM_MEMBERS, 0)  AS INCOME_PER_PERSON
FROM app_all;
