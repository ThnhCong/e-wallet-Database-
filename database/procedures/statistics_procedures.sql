USE ewallet;
DROP PROCEDURE IF EXISTS sp_user_statistics;
DROP PROCEDURE IF EXISTS sp_bank_statistics;
DROP PROCEDURE IF EXISTS sp_admin_system_statistics;
DELIMITER $$
-- Per-currency statistics of one user over a date range (NULL bounds = unlimited).
-- Only SUCCESS transactions are summed; failed ones are only counted.
CREATE PROCEDURE sp_user_statistics(IN p_user_id BIGINT UNSIGNED, IN p_from DATE, IN p_to DATE)
BEGIN
  SELECT w.currency,
         COUNT(DISTINCT w.wallet_id)                                                              AS wallet_count,
         COALESCE(SUM(CASE WHEN t.status='SUCCESS' AND t.type='DEPOSIT'  THEN t.amount END),0)    AS total_deposit,
         COALESCE(SUM(CASE WHEN t.status='SUCCESS' AND t.type='WITHDRAW' THEN t.amount END),0)    AS total_withdraw,
         COALESCE(SUM(CASE WHEN t.status='SUCCESS' AND t.type='TRANSFER' AND t.sender_id=w.wallet_id   THEN t.amount END),0) AS total_transfer_out,
         COALESCE(SUM(CASE WHEN t.status='SUCCESS' AND t.type='TRANSFER' AND t.receiver_id=w.wallet_id THEN t.amount END),0) AS total_transfer_in,
         COALESCE(SUM(t.status='SUCCESS'),0)                                                      AS success_count,
         COALESCE(SUM(t.status='FAIL'),0)                                                         AS fail_count
  FROM wallets w
  LEFT JOIN transactions t
         ON (t.sender_id=w.wallet_id OR t.receiver_id=w.wallet_id)
        AND (p_from IS NULL OR t.created_at >= p_from)
        AND (p_to   IS NULL OR t.created_at <  DATE_ADD(p_to, INTERVAL 1 DAY))
  WHERE w.user_id=p_user_id
  GROUP BY w.currency
  ORDER BY w.currency;
END$$

-- For every partner bank: how many wallets and how many distinct users are linked.
-- (users and banks are related N:M through wallets and bank_accounts.)
CREATE PROCEDURE sp_bank_statistics()
BEGIN
  SELECT b.bank_id,b.name AS bank_name,b.cooperated_at,b.is_valid,
         COUNT(ba.bank_account_id)   AS linked_wallets,
         COUNT(DISTINCT w.user_id)   AS linked_users
  FROM banks b
  LEFT JOIN bank_accounts ba ON ba.bank_id=b.bank_id AND ba.status='SUCCESS'
  LEFT JOIN wallets w ON w.wallet_id=ba.wallet_id
  GROUP BY b.bank_id,b.name,b.cooperated_at,b.is_valid
  ORDER BY linked_wallets DESC,b.name;
END$$

-- One-row overview of the whole system for the administrator dashboard.
CREATE PROCEDURE sp_admin_system_statistics()
BEGIN
  SELECT (SELECT COUNT(*) FROM users)                                        AS users,
         (SELECT COUNT(*) FROM user_profiles)                                AS profiles,
         (SELECT COUNT(*) FROM wallets)                                      AS wallets,
         (SELECT COUNT(*) FROM wallets WHERE status='LOCKED')                AS locked_wallets,
         (SELECT COUNT(*) FROM banks)                                        AS banks,
         (SELECT COUNT(*) FROM banks WHERE is_valid=TRUE) AS active_banks,
         (SELECT COUNT(*) FROM banks WHERE is_valid=FALSE) AS inactive_banks,
         (SELECT COUNT(*) FROM bank_accounts)                                AS bank_accounts,
         (SELECT COUNT(*) FROM transactions WHERE status='SUCCESS')          AS tx_success,
         (SELECT COUNT(*) FROM transactions WHERE status='FAIL')             AS tx_fail,
         (SELECT COUNT(*) FROM transactions WHERE status='PENDING')          AS tx_pending,
         (SELECT COALESCE(SUM(amount),0) FROM transactions WHERE status='SUCCESS' AND type='DEPOSIT'
            AND receiver_id IN (SELECT wallet_id FROM wallets WHERE currency='VND'))  AS deposit_volume_vnd,
         (SELECT COALESCE(SUM(amount),0) FROM transactions WHERE status='SUCCESS' AND type='DEPOSIT'
            AND receiver_id IN (SELECT wallet_id FROM wallets WHERE currency='USD'))  AS deposit_volume_usd;
END$$
DELIMITER ;
