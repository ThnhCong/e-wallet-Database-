USE ewallet;
DROP TRIGGER IF EXISTS trg_wallets_before_delete;
DELIMITER $$
CREATE TRIGGER trg_wallets_before_delete
BEFORE DELETE ON wallets
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1
                 FROM transactions
                WHERE sender_id = OLD.wallet_id
                   OR receiver_id = OLD.wallet_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Wallet with transaction history cannot be deleted';
    END IF;
END$$