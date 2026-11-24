-- E-WALLET STORED PROCEDURES
-- Run this file once AFTER All_Migrations.sql and All_Triggers.sql.
-- MySQL Workbench: open this file and execute the complete script.
USE ewallet;
SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;


-- ==================== user_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_user_create;
DROP PROCEDURE IF EXISTS sp_user_get_by_phone;
DROP PROCEDURE IF EXISTS sp_user_get_with_hash;
DROP PROCEDURE IF EXISTS sp_user_get_by_id;
DROP PROCEDURE IF EXISTS sp_user_update_profile;
DROP PROCEDURE IF EXISTS sp_user_update_password;
DELIMITER $$
CREATE PROCEDURE sp_user_create(IN p_user_name VARCHAR(100), IN p_password_hash VARCHAR(255), IN p_email VARCHAR(255), IN p_phone VARCHAR(20))
BEGIN
  INSERT INTO users(user_name,password_hash,email,phone) VALUES(p_user_name,p_password_hash,p_email,p_phone);
  SELECT LAST_INSERT_ID() AS user_id;
END$$
CREATE PROCEDURE sp_user_get_by_phone(IN p_phone VARCHAR(20))
BEGIN
  SELECT user_id,user_name,password_hash,email,phone FROM users WHERE phone=p_phone LIMIT 1;
END$$
CREATE PROCEDURE sp_user_get_with_hash(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT user_id,user_name,password_hash,email,phone FROM users WHERE user_id=p_user_id LIMIT 1;
END$$
CREATE PROCEDURE sp_user_get_by_id(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT user_id,user_name,email,phone FROM users WHERE user_id=p_user_id LIMIT 1;
END$$
CREATE PROCEDURE sp_user_update_profile(IN p_user_id BIGINT UNSIGNED, IN p_user_name VARCHAR(100), IN p_email VARCHAR(255), IN p_phone VARCHAR(20))
BEGIN
  UPDATE users SET user_name=p_user_name,email=p_email,phone=p_phone WHERE user_id=p_user_id;
  SELECT ROW_COUNT() AS affected_rows;
END$$
CREATE PROCEDURE sp_user_update_password(IN p_user_id BIGINT UNSIGNED, IN p_password_hash VARCHAR(255))
BEGIN
  UPDATE users SET password_hash=p_password_hash WHERE user_id=p_user_id;
  SELECT ROW_COUNT() AS affected_rows;
END$$
DELIMITER ;

-- ==================== wallet_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_wallet_create;
DROP PROCEDURE IF EXISTS sp_wallet_get_by_id;
DROP PROCEDURE IF EXISTS sp_wallet_list_by_user;
DROP PROCEDURE IF EXISTS sp_wallet_list_all;
DROP PROCEDURE IF EXISTS sp_wallet_lock_many;
DROP PROCEDURE IF EXISTS sp_wallet_set_status;
DELIMITER $$
CREATE PROCEDURE sp_wallet_create(IN p_user_id BIGINT UNSIGNED, IN p_currency VARCHAR(3))
BEGIN
  INSERT INTO wallets(user_id,currency) VALUES(p_user_id,p_currency);
  SELECT LAST_INSERT_ID() AS wallet_id;
END$$
CREATE PROCEDURE sp_wallet_get_by_id(IN p_wallet_id BIGINT UNSIGNED)
BEGIN
  SELECT w.wallet_id,w.user_id,u.user_name,w.balance,w.currency,w.limit_week,w.remain_limit_week,w.status,w.created_at
  FROM wallets w INNER JOIN users u ON u.user_id=w.user_id WHERE w.wallet_id=p_wallet_id LIMIT 1;
END$$
CREATE PROCEDURE sp_wallet_list_by_user(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT wallet_id,balance,currency,limit_week,remain_limit_week,status,created_at
  FROM wallets WHERE user_id=p_user_id ORDER BY wallet_id;
END$$
CREATE PROCEDURE sp_wallet_list_all(IN p_user_id BIGINT UNSIGNED, IN p_limit INT)
BEGIN
  SELECT w.wallet_id,w.user_id,u.user_name,w.balance,w.currency,w.limit_week,w.remain_limit_week,w.status,w.created_at
  FROM wallets w INNER JOIN users u ON u.user_id=w.user_id
  WHERE p_user_id IS NULL OR w.user_id=p_user_id
  ORDER BY w.wallet_id LIMIT p_limit;
END$$
CREATE PROCEDURE sp_wallet_lock_many(IN p_wallet_id_1 BIGINT UNSIGNED, IN p_wallet_id_2 BIGINT UNSIGNED)
BEGIN
  SELECT wallet_id,user_id,status,currency FROM wallets
  WHERE (p_wallet_id_1 IS NOT NULL AND wallet_id=p_wallet_id_1)
     OR (p_wallet_id_2 IS NOT NULL AND wallet_id=p_wallet_id_2)
  ORDER BY wallet_id FOR UPDATE;
END$$
CREATE PROCEDURE sp_wallet_set_status(IN p_wallet_id BIGINT UNSIGNED, IN p_status VARCHAR(10))
BEGIN
  UPDATE wallets SET status=p_status WHERE wallet_id=p_wallet_id;
  SELECT ROW_COUNT() AS affected_rows;
END$$
DELIMITER ;

-- ==================== transaction_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_transaction_create;
DROP PROCEDURE IF EXISTS sp_transaction_set_status;
DROP PROCEDURE IF EXISTS sp_transaction_get;
DROP PROCEDURE IF EXISTS sp_transaction_list_user;
DROP PROCEDURE IF EXISTS sp_transaction_list_all;
DELIMITER $$
CREATE PROCEDURE sp_transaction_create(IN p_sender_id BIGINT UNSIGNED, IN p_receiver_id BIGINT UNSIGNED, IN p_type VARCHAR(10), IN p_amount DECIMAL(15,2))
BEGIN
  INSERT INTO transactions(sender_id,receiver_id,type,amount)
  VALUES(p_sender_id,p_receiver_id,p_type,p_amount);
  SELECT LAST_INSERT_ID() AS transaction_id;
END$$
CREATE PROCEDURE sp_transaction_set_status(IN p_transaction_id BIGINT UNSIGNED, IN p_status VARCHAR(10))
BEGIN
  UPDATE transactions SET status=p_status
  WHERE transaction_id=p_transaction_id AND status='PENDING';
  SELECT ROW_COUNT() AS affected_rows;
END$$
CREATE PROCEDURE sp_transaction_get(IN p_transaction_id BIGINT UNSIGNED)
BEGIN
  SELECT t.transaction_id,t.type,t.amount,t.status,t.sender_id,t.receiver_id,t.created_at,
         s.user_id AS sender_user_id,r.user_id AS receiver_user_id
  FROM transactions t
  LEFT JOIN wallets s ON s.wallet_id=t.sender_id
  LEFT JOIN wallets r ON r.wallet_id=t.receiver_id
  WHERE t.transaction_id=p_transaction_id LIMIT 1;
END$$
CREATE PROCEDURE sp_transaction_list_user(IN p_user_id BIGINT UNSIGNED, IN p_type VARCHAR(10), IN p_status VARCHAR(10), IN p_limit INT)
BEGIN
  SELECT t.transaction_id,t.type,t.amount,t.status,t.sender_id,t.receiver_id,t.created_at
  FROM transactions t
  LEFT JOIN wallets s ON s.wallet_id=t.sender_id
  LEFT JOIN wallets r ON r.wallet_id=t.receiver_id
  WHERE (s.user_id=p_user_id OR r.user_id=p_user_id)
    AND (p_type IS NULL OR t.type=p_type)
    AND (p_status IS NULL OR t.status=p_status)
  ORDER BY t.created_at DESC,t.transaction_id DESC LIMIT p_limit;
END$$
CREATE PROCEDURE sp_transaction_list_all(IN p_type VARCHAR(10), IN p_status VARCHAR(10), IN p_limit INT)
BEGIN
  SELECT t.transaction_id,t.type,t.amount,t.status,t.sender_id,t.receiver_id,t.created_at
  FROM transactions t
  WHERE (p_type IS NULL OR t.type=p_type)
    AND (p_status IS NULL OR t.status=p_status)
  ORDER BY t.created_at DESC,t.transaction_id DESC LIMIT p_limit;
END$$
DELIMITER ;

-- ==================== audit_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_audit_create;
DROP PROCEDURE IF EXISTS sp_audit_list;
DELIMITER $$
CREATE PROCEDURE sp_audit_create(IN p_user_id BIGINT UNSIGNED, IN p_wallet_id BIGINT UNSIGNED, IN p_transaction_id BIGINT UNSIGNED, IN p_action VARCHAR(100))
BEGIN
  INSERT INTO audit_logs(user_id,wallet_id,transaction_id,action)
  VALUES(p_user_id,p_wallet_id,p_transaction_id,p_action);
  SELECT LAST_INSERT_ID() AS audit_log_id;
END$$
CREATE PROCEDURE sp_audit_list(IN p_user_id BIGINT UNSIGNED, IN p_action VARCHAR(100), IN p_limit INT)
BEGIN
  SELECT audit_log_id,user_id,wallet_id,transaction_id,action,created_at
  FROM audit_logs
  WHERE (p_user_id IS NULL OR user_id=p_user_id)
    AND (p_action IS NULL OR action=p_action)
  ORDER BY created_at DESC,audit_log_id DESC LIMIT p_limit;
END$$
DELIMITER ;

-- ==================== user_profile_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_user_profile_get;
DROP PROCEDURE IF EXISTS sp_user_profile_save;
DROP PROCEDURE IF EXISTS sp_admin_list_user_profiles;
DELIMITER $$
CREATE PROCEDURE sp_user_profile_get(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT user_profile_id,user_id,date_of_birth,age,sex,address,job,country,created_at
  FROM user_profiles WHERE user_id=p_user_id LIMIT 1;
END$$
CREATE PROCEDURE sp_user_profile_save(IN p_user_id BIGINT UNSIGNED, IN p_date_of_birth DATE, IN p_age TINYINT UNSIGNED, IN p_sex VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
                                      IN p_address VARCHAR(255), IN p_job VARCHAR(100), IN p_country VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci)
BEGIN
  DECLARE v_rows INT DEFAULT 0;
  -- created_at is set only when the profile is first inserted.
  -- On duplicate key (profile already exists), it is deliberately preserved.
  INSERT INTO user_profiles(user_id,date_of_birth,age,sex,address,job,country,created_at)
  VALUES(p_user_id,p_date_of_birth,p_age,p_sex,p_address,p_job,p_country,CURRENT_TIMESTAMP)
  ON DUPLICATE KEY UPDATE
      date_of_birth=VALUES(date_of_birth),
      age=VALUES(age),
      sex=VALUES(sex),
      address=VALUES(address),
      job=VALUES(job),
      country=VALUES(country);
  SET v_rows = ROW_COUNT();
  SELECT user_profile_id, (v_rows = 1) AS created FROM user_profiles WHERE user_id=p_user_id;
END$$
-- Admin listing always returns one result row, even when there are no profiles
-- or the requested page is outside the current range. In that case the profile
-- columns are NULL and total_count still contains the real filtered count.
CREATE PROCEDURE sp_admin_list_user_profiles(
    IN p_search VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, IN p_sex VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, IN p_country VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
    IN p_sort_by VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, IN p_sort_order VARCHAR(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
    IN p_limit INT, IN p_offset INT
)
BEGIN
    SELECT page_rows.user_profile_id,
           page_rows.user_id,
           page_rows.user_name,
           page_rows.email,
           page_rows.phone,
           page_rows.date_of_birth,
           page_rows.age,
           page_rows.sex,
           page_rows.address,
           page_rows.job,
           page_rows.country,
           page_rows.created_at,
           totals.total_count
    FROM (
        SELECT COUNT(*) AS total_count
        FROM user_profiles p
        INNER JOIN users u ON u.user_id = p.user_id
        WHERE (p_search IS NULL
               OR (CAST(p.user_id AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.user_name COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.email COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.address COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.job COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci))
          AND (p_sex IS NULL OR (p.sex COLLATE utf8mb4_0900_ai_ci) = (p_sex COLLATE utf8mb4_0900_ai_ci))
          AND (p_country IS NULL OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_country, '%') COLLATE utf8mb4_0900_ai_ci))
    ) AS totals
    LEFT JOIN (
        SELECT p.user_profile_id, p.user_id, u.user_name, u.email, u.phone,
               p.date_of_birth, p.age, p.sex, p.address, p.job, p.country, p.created_at
        FROM user_profiles p
        INNER JOIN users u ON u.user_id = p.user_id
        WHERE (p_search IS NULL
               OR (CAST(p.user_id AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.user_name COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.email COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.address COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.job COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci))
          AND (p_sex IS NULL OR (p.sex COLLATE utf8mb4_0900_ai_ci) = (p_sex COLLATE utf8mb4_0900_ai_ci))
          AND (p_country IS NULL OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_country, '%') COLLATE utf8mb4_0900_ai_ci))
        ORDER BY
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('created_at' COLLATE utf8mb4_0900_ai_ci) AND p.created_at IS NULL THEN 1 ELSE 0 END ASC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('created_at' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('ASC' COLLATE utf8mb4_0900_ai_ci) THEN p.created_at END ASC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('created_at' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('DESC' COLLATE utf8mb4_0900_ai_ci) THEN p.created_at END DESC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('user_id' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('ASC' COLLATE utf8mb4_0900_ai_ci) THEN p.user_id END ASC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('user_id' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('DESC' COLLATE utf8mb4_0900_ai_ci) THEN p.user_id END DESC,
            p.user_profile_id DESC
        LIMIT p_limit OFFSET p_offset
    ) AS page_rows ON TRUE;
END$$
DELIMITER ;


-- ==================== bank_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_admin_list_users;
DROP PROCEDURE IF EXISTS sp_admin_bank_create;
DROP PROCEDURE IF EXISTS sp_admin_bank_set_valid;
DROP PROCEDURE IF EXISTS sp_bank_list;
DROP PROCEDURE IF EXISTS sp_admin_bank_list;
DROP PROCEDURE IF EXISTS sp_bank_get;
DROP PROCEDURE IF EXISTS sp_bank_account_link;
DROP PROCEDURE IF EXISTS sp_bank_account_unlink;
DROP PROCEDURE IF EXISTS sp_bank_account_has_active_link;
DROP PROCEDURE IF EXISTS sp_bank_account_list_by_user;
DROP PROCEDURE IF EXISTS sp_bank_account_list_all;
DELIMITER $$
CREATE PROCEDURE sp_bank_list()
BEGIN SELECT bank_id,name,cooperated_at,is_valid FROM banks WHERE is_valid=TRUE ORDER BY name; END$$
CREATE PROCEDURE sp_admin_bank_list()
BEGIN SELECT bank_id,name,cooperated_at,is_valid FROM banks ORDER BY name; END$$
CREATE PROCEDURE sp_admin_bank_create(IN p_name VARCHAR(100))
BEGIN
 IF p_name IS NULL OR CHAR_LENGTH(TRIM(p_name))=0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Bank name is required'; END IF;
 INSERT INTO banks(name,is_valid) VALUES(TRIM(p_name),TRUE);
 SELECT bank_id,name,cooperated_at,is_valid FROM banks WHERE bank_id=LAST_INSERT_ID();
END$$
CREATE PROCEDURE sp_admin_bank_set_valid(IN p_bank_id BIGINT UNSIGNED, IN p_is_valid BOOLEAN)
BEGIN
 IF NOT EXISTS(SELECT 1 FROM banks WHERE bank_id=p_bank_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Bank does not exist'; END IF;
 UPDATE banks SET is_valid=p_is_valid WHERE bank_id=p_bank_id;
 SELECT bank_id,name,cooperated_at,is_valid FROM banks WHERE bank_id=p_bank_id;
END$$
CREATE PROCEDURE sp_bank_get(IN p_bank_id BIGINT UNSIGNED)
BEGIN SELECT bank_id,name,cooperated_at,is_valid FROM banks WHERE bank_id=p_bank_id LIMIT 1; END$$
CREATE PROCEDURE sp_bank_account_link(IN p_wallet_id BIGINT UNSIGNED, IN p_bank_id BIGINT UNSIGNED, IN p_account_number VARCHAR(34))
BEGIN
 IF NOT EXISTS(SELECT 1 FROM banks WHERE bank_id=p_bank_id AND is_valid=TRUE) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='This partner bank is no longer active'; END IF;
 IF NOT EXISTS(SELECT 1 FROM wallets WHERE wallet_id=p_wallet_id AND status='ACTIVE') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Wallet does not exist or is locked'; END IF;
 IF p_account_number IS NULL OR p_account_number NOT REGEXP '^[0-9]{6,34}$' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Bank account number must contain 6-34 digits'; END IF;
 IF EXISTS(SELECT 1 FROM bank_accounts WHERE bank_id=p_bank_id AND account_number=p_account_number AND status='SUCCESS') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='This bank account number is already linked'; END IF;
 IF EXISTS(SELECT 1 FROM bank_accounts WHERE wallet_id=p_wallet_id AND bank_id=p_bank_id AND status='SUCCESS') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='This wallet is already linked to this bank'; END IF;
 INSERT INTO bank_accounts(wallet_id,bank_id,account_number,status) VALUES(p_wallet_id,p_bank_id,p_account_number,'SUCCESS');
 SELECT bank_account_id,account_number FROM bank_accounts WHERE wallet_id=p_wallet_id AND bank_id=p_bank_id AND status='SUCCESS' ORDER BY bank_account_id DESC LIMIT 1;
END$$
CREATE PROCEDURE sp_bank_account_unlink(IN p_user_id BIGINT UNSIGNED, IN p_bank_account_id BIGINT UNSIGNED)
BEGIN
 DECLARE v_wallet_id BIGINT UNSIGNED DEFAULT NULL;
 DECLARE v_rows INT DEFAULT 0;
 DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_wallet_id=NULL;
 SELECT ba.wallet_id INTO v_wallet_id
   FROM bank_accounts ba
   INNER JOIN wallets w ON w.wallet_id=ba.wallet_id
  WHERE ba.bank_account_id=p_bank_account_id
    AND w.user_id=p_user_id
    AND ba.status='SUCCESS'
  LIMIT 1 FOR UPDATE;
 IF v_wallet_id IS NULL THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Active bank link not found';
 END IF;
 UPDATE bank_accounts SET status='CANCELLED'
  WHERE bank_account_id=p_bank_account_id AND status='SUCCESS';
 SET v_rows=ROW_COUNT();
 SELECT v_rows AS affected_rows,v_wallet_id AS wallet_id;
END$$
CREATE PROCEDURE sp_bank_account_has_active_link(IN p_wallet_id BIGINT UNSIGNED)
BEGIN SELECT EXISTS(SELECT 1 FROM bank_accounts ba INNER JOIN banks b ON b.bank_id=ba.bank_id WHERE ba.wallet_id=p_wallet_id AND ba.status='SUCCESS' AND b.is_valid=TRUE) AS has_active_link; END$$
CREATE PROCEDURE sp_bank_account_list_by_user(IN p_user_id BIGINT UNSIGNED)
BEGIN
 SELECT ba.bank_account_id,ba.wallet_id,w.currency,ba.bank_id,b.name AS bank_name,ba.account_number,ba.status,ba.linked_at,b.is_valid
 FROM bank_accounts ba INNER JOIN wallets w ON w.wallet_id=ba.wallet_id INNER JOIN banks b ON b.bank_id=ba.bank_id
 WHERE w.user_id=p_user_id ORDER BY ba.linked_at DESC,ba.bank_account_id DESC;
END$$
CREATE PROCEDURE sp_bank_account_list_all(IN p_limit INT)
BEGIN
 SELECT ba.bank_account_id,ba.wallet_id,w.user_id,u.user_name,ba.bank_id,b.name AS bank_name,ba.account_number,ba.status,ba.linked_at,b.is_valid
 FROM bank_accounts ba INNER JOIN wallets w ON w.wallet_id=ba.wallet_id INNER JOIN users u ON u.user_id=w.user_id INNER JOIN banks b ON b.bank_id=ba.bank_id
 ORDER BY ba.linked_at DESC,ba.bank_account_id DESC LIMIT p_limit;
END$$
DELIMITER ;


-- ==================== admin_procedures.sql ====================
-- Restore the procedure delimiter after the preceding section.
DELIMITER $$
CREATE PROCEDURE sp_admin_list_users(IN p_limit INT)
BEGIN
  SELECT u.user_id,u.user_name,u.email,u.phone,
         COUNT(w.wallet_id) AS wallet_count,
         EXISTS(SELECT 1 FROM user_profiles p WHERE p.user_id=u.user_id) AS has_profile
    FROM users u
    LEFT JOIN wallets w ON w.user_id=u.user_id
   GROUP BY u.user_id,u.user_name,u.email,u.phone
   ORDER BY u.user_id
   LIMIT p_limit;
END$$
DELIMITER ;

-- ==================== statistics_procedures.sql ====================
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
  LEFT JOIN bank_accounts ba ON ba.bank_id=b.bank_id AND ba.status='SUCCESS' AND b.is_valid=TRUE
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
