-- One row per applicant: summary of their loans at other lenders.
CREATE OR REPLACE TABLE bureau_agg AS

-- Hop 1: monthly history -> one row per bureau LOAN
WITH bb AS (
    SELECT
        SK_ID_BUREAU,
        COUNT(*) AS n_months,
        SUM(CASE WHEN STATUS IN ('1','2','3','4','5') THEN 1 ELSE 0 END) AS n_late_months
    FROM 'data/parquet/bureau_balance.parquet'
    GROUP BY SK_ID_BUREAU
)

-- Hop 2: loans -> one row per APPLICANT
SELECT
    b.SK_ID_CURR,
    COUNT(*) AS BUREAU_LOAN_COUNT,
    SUM(CASE WHEN b.CREDIT_ACTIVE = 'Active' THEN 1 ELSE 0 END) AS BUREAU_ACTIVE_COUNT,

        -- Only active loans where the debt is known, on BOTH top and bottom
    SUM(CASE WHEN b.CREDIT_ACTIVE = 'Active' AND b.AMT_CREDIT_SUM_DEBT IS NOT NULL
             THEN b.AMT_CREDIT_SUM_DEBT END)
      / NULLIF(SUM(CASE WHEN b.CREDIT_ACTIVE = 'Active' AND b.AMT_CREDIT_SUM_DEBT IS NOT NULL
             THEN b.AMT_CREDIT_SUM END), 0)
      AS BUREAU_DEBT_TO_CREDIT,

    MAX(b.CREDIT_DAY_OVERDUE)     AS BUREAU_MAX_DAYS_OVERDUE,
    MAX(b.AMT_CREDIT_MAX_OVERDUE) AS BUREAU_MAX_AMT_OVERDUE,

    SUM(bb.n_late_months) / NULLIF(SUM(bb.n_months), 0) AS BUREAU_LATE_MONTH_SHARE,

    -MIN(b.DAYS_CREDIT) / 365.25 AS BUREAU_YEARS_SINCE_FIRST,
    -MAX(b.DAYS_CREDIT) / 365.25 AS BUREAU_YEARS_SINCE_LAST
FROM 'data/parquet/bureau.parquet' AS b
LEFT JOIN bb ON b.SK_ID_BUREAU = bb.SK_ID_BUREAU
GROUP BY b.SK_ID_CURR;
