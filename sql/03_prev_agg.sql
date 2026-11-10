-- One row per applicant: their earlier applications to Home Credit.
CREATE OR REPLACE TABLE prev_agg AS
SELECT
    SK_ID_CURR,
    COUNT(*) AS PREV_APP_COUNT,

    -- Average of a 0/1 flag = a rate (same trick as AVG(TARGET))
    AVG(CASE WHEN NAME_CONTRACT_STATUS = 'Refused' THEN 1 ELSE 0 END)
        AS PREV_REFUSAL_RATE,

    -- Only approved applications; NULLIF guards against AMT_APPLICATION = 0
    AVG(CASE WHEN NAME_CONTRACT_STATUS = 'Approved'
             THEN AMT_CREDIT / NULLIF(AMT_APPLICATION, 0) END)
        AS PREV_GRANTED_TO_REQUESTED,

    -MAX(DAYS_DECISION) AS PREV_DAYS_SINCE_LAST_APP
FROM 'data/parquet/previous_application.parquet'
GROUP BY SK_ID_CURR;
