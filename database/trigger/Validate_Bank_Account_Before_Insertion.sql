-- Validate_Bank_Account_Before_Insertion
-- BEFORE INSERT on bank_accounts: a wallet can be linked to a bank only if
-- the wallet exists and is ACTIVE, the bank exists and the wallet is not already
-- linked to that bank. A new link always starts as SUCCESS or PENDING (never FAIL).
USE ewallet;
DROP TRIGGER IF EXISTS trg_bank_accounts_before_insert;
DELIMITER $$
CREATE TRIGGER trg_bank_accounts_before_insert
BEFORE INSERT ON bank_accounts
FOR EACH ROW
BEGIN
    DECLARE v_w_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_bank_id  BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_dup      BIGINT UNSIGNED DEFAULT NULL;
    DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;   -- SELECT ... INTO without a row is not an error here

    SELECT status INTO v_w_status FROM wallets WHERE wallet_id = NEW.wallet_id;
    IF v_w_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Wallet does not exist';
    END IF;
    IF v_w_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Wallet is locked';
    END IF;

    SELECT bank_id INTO v_bank_id FROM banks WHERE bank_id = NEW.bank_id;
    IF v_bank_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank does not exist';
    END IF;

    SELECT bank_account_id INTO v_dup FROM bank_accounts
     WHERE wallet_id = NEW.wallet_id AND bank_id = NEW.bank_id LIMIT 1;
    IF v_dup IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Wallet is already linked to this bank';
    END IF;

    IF NEW.status = 'FAIL' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A new bank link cannot start as FAIL';
    END IF;
END$$
DELIMITER ;
