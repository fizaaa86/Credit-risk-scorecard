-- One row per applicant: how they repaid their previous Home Credit loans.
CREATE OR REPLACE TABLE inst_agg AS

-- Step 1: payment rows -> one row per INSTALLMENT (combine split payments)
WITH per_installment AS (
    SELECT
        SK_ID_CURR, SK_ID_PREV, NUM_INSTALMENT_VERSION, NUM_INSTALMENT_NUMBER,
        MIN(DAYS_INSTALMENT)    AS DAYS_DUE,
        MAX(DAYS_ENTRY_PAYMENT) AS DAYS_PAID,     -- date of the LAST part
        MIN(AMT_INSTALMENT)     AS AMT_DUE,
        SUM(AMT_PAYMENT)        AS AMT_PAID       -- total of all parts
    FROM 'data/parquet/installments_payments.parquet'
    WHERE DAYS_ENTRY_PAYMENT IS NOT NULL          -- skip installments not paid yet
    GROUP BY SK_ID_CURR, SK_ID_PREV, NUM_INSTALMENT_VERSION, NUM_INSTALMENT_NUMBER
),

-- Step 2: flag each installment, and rank by recency within each applicant
flagged AS (
    SELECT
        SK_ID_CURR,
        GREATEST(DAYS_PAID - DAYS_DUE, 0)              AS DAYS_LATE,
        CASE WHEN DAYS_PAID > DAYS_DUE THEN 1 ELSE 0 END AS IS_LATE,
        CASE WHEN AMT_PAID  < AMT_DUE  THEN 1 ELSE 0 END AS IS_SHORT,
        ROW_NUMBER() OVER (PARTITION BY SK_ID_CURR ORDER BY DAYS_DUE DESC) AS RECENCY_RANK
    FROM per_installment
)

-- Step 3: installments -> one row per APPLICANT
SELECT
    SK_ID_CURR,
    COUNT(*)       AS INST_COUNT,
    AVG(IS_LATE)   AS INSTALLMENT_LATE_SHARE,
    AVG(DAYS_LATE) AS INST_MEAN_DAYS_LATE,
    MAX(DAYS_LATE) AS INST_MAX_DAYS_LATE,
    AVG(IS_SHORT)  AS INST_SHORT_SHARE,
    AVG(CASE WHEN RECENCY_RANK <= 12 THEN IS_LATE   END) AS INST_LATE_SHARE_LAST12,
    AVG(CASE WHEN RECENCY_RANK <= 12 THEN DAYS_LATE END) AS INST_MEAN_DAYS_LATE_LAST12,
    AVG(CASE WHEN RECENCY_RANK <= 12 THEN IS_SHORT  END) AS INST_SHORT_SHARE_LAST12
FROM flagged
GROUP BY SK_ID_CURR;
