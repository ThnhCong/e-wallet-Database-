USE ewallet;
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
