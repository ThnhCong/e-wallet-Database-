USE ewallet;
DROP TRIGGER IF EXISTS trg_transactions_before_delete;
DELIMITER $$
CREATE TRIGGER trg_transactions_before_delete
BEFORE DELETE ON transactions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Transactions cannot be deleted';
END$$