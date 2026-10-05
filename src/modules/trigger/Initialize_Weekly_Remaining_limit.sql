USE ewallet;
DROP TRIGGER IF EXISTS trg_wallets_before_insert;
DELIMITER $$
CREATE TRIGGER trg_wallets_before_insert
BEFORE INSERT ON wallets
FOR EACH ROW
BEGIN
    SET NEW.remain_limit_week = NEW.limit_week;
END$$