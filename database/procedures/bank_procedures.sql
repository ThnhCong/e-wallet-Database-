USE ewallet;
DROP PROCEDURE IF EXISTS sp_admin_bank_create;
DROP PROCEDURE IF EXISTS sp_admin_bank_delete;
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
 DECLARE v_wallet_id BIGINT UNSIGNED DEFAULT NULL; DECLARE v_rows INT DEFAULT 0;
 DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_wallet_id=NULL;
 SELECT ba.wallet_id INTO v_wallet_id FROM bank_accounts ba INNER JOIN wallets w ON w.wallet_id=ba.wallet_id WHERE ba.bank_account_id=p_bank_account_id AND w.user_id=p_user_id AND ba.status='SUCCESS' LIMIT 1;
 IF v_wallet_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Active bank link not found'; END IF;
 UPDATE bank_accounts SET status='CANCELLED' WHERE bank_account_id=p_bank_account_id AND status='SUCCESS';
 SET v_rows=ROW_COUNT(); SELECT v_rows AS affected_rows,v_wallet_id AS wallet_id;
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
