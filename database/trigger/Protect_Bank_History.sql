USE ewallet;

-- Historical catalogues and links must never be physically deleted.
USE ewallet;
DROP TRIGGER IF EXISTS trg_banks_before_delete;
DROP TRIGGER IF EXISTS trg_bank_accounts_before_delete;
DELIMITER $$
CREATE TRIGGER trg_banks_before_delete BEFORE DELETE ON banks FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Partner banks cannot be deleted; set is_valid=FALSE instead'; END$$
CREATE TRIGGER trg_bank_accounts_before_delete BEFORE DELETE ON bank_accounts FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Bank links cannot be deleted; cancel the link instead'; END$$
DELIMITER ;

