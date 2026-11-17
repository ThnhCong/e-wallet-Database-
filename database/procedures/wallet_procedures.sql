USE ewallet;
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
