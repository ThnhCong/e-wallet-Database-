USE ewallet;
DROP PROCEDURE IF EXISTS sp_admin_bank_create;
DROP PROCEDURE IF EXISTS sp_admin_bank_delete;
DROP PROCEDURE IF EXISTS sp_bank_list;
DROP PROCEDURE IF EXISTS sp_bank_get;
DROP PROCEDURE IF EXISTS sp_bank_account_link;
DROP PROCEDURE IF EXISTS sp_bank_account_list_by_user;
DROP PROCEDURE IF EXISTS sp_bank_account_list_all;
DELIMITER $$
CREATE PROCEDURE sp_bank_list()
BEGIN
  SELECT bank_id,name,cooperated_at FROM banks ORDER BY name;
END$$
-- Admin-only operations are protected by the AdminService authorization check.
CREATE PROCEDURE sp_admin_bank_create(IN p_name VARCHAR(100))
BEGIN
  IF p_name IS NULL OR CHAR_LENGTH(TRIM(p_name)) = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank name is required';
  END IF;
  INSERT INTO banks(name) VALUES(TRIM(p_name));
  SELECT bank_id,name,cooperated_at FROM banks WHERE bank_id=LAST_INSERT_ID();
END$$
CREATE PROCEDURE sp_admin_bank_delete(IN p_bank_id BIGINT UNSIGNED)
BEGIN
  IF NOT EXISTS (SELECT 1 FROM banks WHERE bank_id=p_bank_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank does not exist';
  END IF;
  IF EXISTS (SELECT 1 FROM bank_accounts WHERE bank_id=p_bank_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank has linked accounts';
  END IF;
  DELETE FROM banks WHERE bank_id=p_bank_id;
  SELECT p_bank_id AS bank_id;
END$$
CREATE PROCEDURE sp_bank_get(IN p_bank_id BIGINT UNSIGNED)
BEGIN
  SELECT bank_id,name,cooperated_at FROM banks WHERE bank_id=p_bank_id LIMIT 1;
END$$
-- Links a wallet to a bank. status uses the table default (SUCCESS: the link is simulated).
-- The BEFORE INSERT trigger checks the wallet (exists, ACTIVE), the bank and duplicates.
CREATE PROCEDURE sp_bank_account_link(IN p_wallet_id BIGINT UNSIGNED, IN p_bank_id BIGINT UNSIGNED)
BEGIN
  INSERT INTO bank_accounts(wallet_id,bank_id) VALUES(p_wallet_id,p_bank_id);
  SELECT LAST_INSERT_ID() AS bank_account_id;
END$$
-- All links of the wallets owned by a user (joined with wallet and bank data).
CREATE PROCEDURE sp_bank_account_list_by_user(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT ba.bank_account_id,ba.wallet_id,w.currency,ba.bank_id,b.name AS bank_name,ba.status,ba.linked_at
  FROM bank_accounts ba
  INNER JOIN wallets w ON w.wallet_id=ba.wallet_id
  INNER JOIN banks b ON b.bank_id=ba.bank_id
  WHERE w.user_id=p_user_id
  ORDER BY ba.linked_at DESC,ba.bank_account_id DESC;
END$$
CREATE PROCEDURE sp_bank_account_list_all(IN p_limit INT)
BEGIN
  SELECT ba.bank_account_id,ba.wallet_id,w.user_id,u.user_name,ba.bank_id,b.name AS bank_name,ba.status,ba.linked_at
  FROM bank_accounts ba
  INNER JOIN wallets w ON w.wallet_id=ba.wallet_id
  INNER JOIN users u ON u.user_id=w.user_id
  INNER JOIN banks b ON b.bank_id=ba.bank_id
  ORDER BY ba.linked_at DESC,ba.bank_account_id DESC LIMIT p_limit;
END$$
DELIMITER ;
