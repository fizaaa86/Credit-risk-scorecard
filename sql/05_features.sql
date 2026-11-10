-- Final table: one row per applicant, all features side by side.
CREATE OR REPLACE TABLE features AS
SELECT *
FROM app_clean
LEFT JOIN bureau_agg USING (SK_ID_CURR)
LEFT JOIN prev_agg   USING (SK_ID_CURR)
LEFT JOIN inst_agg   USING (SK_ID_CURR);
