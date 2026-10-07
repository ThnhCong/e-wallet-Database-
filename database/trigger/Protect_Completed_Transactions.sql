USE ewallet;
DROP TRIGGER IF EXISTS trg_transactions_before_update;
DELIMITER $$
CREATE TRIGGER trg_transactions_before_update
BEFORE UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF OLD.status IN ('SUCCESS', 'FAIL') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Completed transactions cannot be modified';
    END IF;

    IF NEW.status NOT IN ('SUCCESS', 'FAIL') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A PENDING transaction can only become SUCCESS or FAIL';
    END IF;

    IF NEW.type <> OLD.type
       OR NEW.amount <> OLD.amount
       OR NOT (NEW.sender_id <=> OLD.sender_id)
       OR NOT (NEW.receiver_id <=> OLD.receiver_id)
       OR NEW.created_at <> OLD.created_at THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only the status of a transaction can be changed';
    END IF;
END$$