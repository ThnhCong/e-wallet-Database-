USE ewallet;
DROP TRIGGER IF EXISTS trg_wallets_before_update;
DELIMITER $$
CREATE TRIGGER trg_wallets_before_update
BEFORE UPDATE ON wallets
FOR EACH ROW
BEGIN
    IF NEW.balance < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Wallet balance cannot be negative';
    END IF;

    IF NEW.balance <> OLD.balance AND IFNULL(@allow_balance_update, 0) <> 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Balance can only be changed by a successful transaction';
    END IF;
END$$