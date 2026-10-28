-- =============================================================================
-- SQL Validation: Referential Integrity and Allowed Value Checks
-- Description: Detects orphaned foreign keys, illegal enumerations, and cross-field rules.
-- =============================================================================

-- 1. Unknown Account Reference (Orphaned Account ID)
WITH unknown_accounts AS (
    SELECT
        st.staging_id,
        st.batch_id,
        COALESCE(st.transaction_id, st.source_record_id) AS record_reference,
        'DQ015' AS rule_id,
        'account_id' AS field_name,
        st.account_id AS invalid_value,
        'CRITICAL' AS severity,
        'Referenced account_id does not exist in dim_accounts dimension: ' || COALESCE(st.account_id, 'NULL') AS issue_description
    FROM stg_transactions st
    LEFT JOIN dim_accounts da ON st.account_id = da.account_id
    WHERE st.account_id IS NOT NULL AND TRIM(st.account_id) <> ''
      AND da.account_id IS NULL
),

-- 2. Invalid Transaction Type or Status Enumeration
invalid_enums AS (
    SELECT
        st.staging_id,
        st.batch_id,
        COALESCE(st.transaction_id, st.source_record_id) AS record_reference,
        'DQ016' AS rule_id,
        'transaction_type,transaction_status' AS field_name,
        'type=' || COALESCE(st.transaction_type, 'NULL') || ', status=' || COALESCE(st.transaction_status, 'NULL') AS invalid_value,
        'HIGH' AS severity,
        'Unrecognized transaction type or status value' AS issue_description
    FROM stg_transactions st
    WHERE (
        st.transaction_type IS NOT NULL
        AND st.transaction_type NOT IN ('DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'REFUND', 'TRANSFER', 'FEE', 'REVERSAL')
    ) OR (
        st.transaction_status IS NOT NULL
        AND st.transaction_status NOT IN ('COMPLETED', 'PENDING', 'FAILED', 'REVERSED', 'CANCELLED')
    )
),

-- 3. Cross-Field: Reversal Missing Original Reference
reversals_missing_ref AS (
    SELECT
        st.staging_id,
        st.batch_id,
        COALESCE(st.transaction_id, st.source_record_id) AS record_reference,
        'DQ017' AS rule_id,
        'reference_id,transaction_type' AS field_name,
        'reference_id=' || COALESCE(st.reference_id, 'NULL') AS invalid_value,
        'HIGH' AS severity,
        'Reversal transaction must supply originating reference_id' AS issue_description
    FROM stg_transactions st
    WHERE st.transaction_type = 'REVERSAL'
      AND (st.reference_id IS NULL OR TRIM(st.reference_id) = '')
)
SELECT * FROM unknown_accounts
UNION ALL
SELECT * FROM invalid_enums
UNION ALL
SELECT * FROM reversals_missing_ref;
