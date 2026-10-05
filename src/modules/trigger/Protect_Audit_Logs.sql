USE ewallet;
DROP TRIGGER IF EXISTS trg_audit_logs_before_update;
DROP TRIGGER IF EXISTS trg_audit_logs_before_delete;
DELIMITER $$
CREATE TRIGGER trg_audit_logs_before_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Audit logs cannot be modified';
END$$

CREATE TRIGGER trg_audit_logs_before_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Audit logs cannot be deleted';
END$$

DELIMITER ;