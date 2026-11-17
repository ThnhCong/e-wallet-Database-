USE ewallet;
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
