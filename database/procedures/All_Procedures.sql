-- E-WALLET STORED PROCEDURES
-- Run this file once AFTER All_Migrations.sql and All_Triggers.sql.
-- MySQL Workbench: open this file and execute the complete script.
USE ewallet;


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

-- ==================== admin_procedures.sql ====================
DROP PROCEDURE IF EXISTS sp_admin_list_users;
DELIMITER $$
CREATE PROCEDURE sp_admin_list_users(IN p_limit INT)
BEGIN
  SELECT u.user_id,u.user_name,u.email,u.phone,COUNT(w.wallet_id) AS wallet_count
  FROM users u LEFT JOIN wallets w ON w.user_id=u.user_id
  GROUP BY u.user_id,u.user_name,u.email,u.phone
  ORDER BY u.user_id LIMIT p_limit;
END$$
DELIMITER ;
