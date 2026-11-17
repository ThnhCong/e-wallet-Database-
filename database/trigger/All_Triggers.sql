-- Prevent_Transaction_Deletion

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
DELIMITER ;


-- Prevent_Wallet_Deletion_with_Transaction_History

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
DELIMITER ;


-- Protect_Audit_Logs

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


-- Protect_Completed_Transactions

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
DELIMITER ;


-- Protect_Wallet_Balance

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
DELIMITER ;


-- Reset_Weekly_Limit

-- LOI CU: file cu co "DELIMITER $$" nhung khong ket thuc bang $$ -> lenh CREATE EVENT khong bao gio
-- duoc thuc thi => event KHONG ton tai. Event nay khong can DELIMITER (chi 1 cau lenh).
SET GLOBAL event_scheduler = ON;
DROP EVENT IF EXISTS ev_reset_weekly_limit;
CREATE EVENT ev_reset_weekly_limit
ON SCHEDULE EVERY 1 WEEK
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL (7 - WEEKDAY(CURRENT_DATE)) DAY)   -- thu Hai ke tiep 00:00
ON COMPLETION PRESERVE
ENABLE
DO
    UPDATE wallets SET remain_limit_week = limit_week WHERE remain_limit_week <> limit_week;
    
    
-- Set_Limit_Via_Currency

DROP TRIGGER IF EXISTS trg_wallets_before_insert;
DELIMITER $$
CREATE TRIGGER trg_wallets_before_insert
BEFORE INSERT ON wallets
FOR EACH ROW
BEGIN
    -- normalise the currency code (e.g. ' usd ' -> 'USD')
    SET NEW.currency = UPPER(TRIM(NEW.currency));

    -- weekly limit is decided by the currency, whatever value was supplied by the caller
    IF NEW.currency = 'VND' THEN
        SET NEW.limit_week = 10000000.00;
    ELSEIF NEW.currency = 'USD' THEN
        SET NEW.limit_week = 500.00;
    ELSE
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Unsupported currency: only VND and USD are supported';
    END IF;

    -- a new wallet always starts with its full weekly limit
    SET NEW.remain_limit_week = NEW.limit_week;
END$$

DELIMITER ;


-- Update_Wallet_Balance_After_Successful_Transaction

DROP TRIGGER IF EXISTS trg_transactions_after_update;
DELIMITER $$
CREATE TRIGGER trg_transactions_after_update
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    DECLARE v_lock_id   BIGINT UNSIGNED;
    DECLARE v_s_status  VARCHAR(10);
    DECLARE v_s_balance DECIMAL(15, 2);
    DECLARE v_s_remain  DECIMAL(15, 2);
    DECLARE v_r_status  VARCHAR(10);

    -- whatever goes wrong, always switch the "balance guard" flag off again
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET @allow_balance_update = 0;
        RESIGNAL;
    END;

    IF OLD.status = 'PENDING' AND NEW.status = 'SUCCESS' THEN

        -- 1. Lock the wallets in ascending wallet_id order (avoids deadlock)
        SELECT wallet_id INTO v_lock_id
          FROM wallets
         WHERE wallet_id = LEAST(COALESCE(NEW.sender_id, NEW.receiver_id),
                                 COALESCE(NEW.receiver_id, NEW.sender_id))
           FOR UPDATE;
        SELECT wallet_id INTO v_lock_id
          FROM wallets
         WHERE wallet_id = GREATEST(COALESCE(NEW.sender_id, NEW.receiver_id),
                                    COALESCE(NEW.receiver_id, NEW.sender_id))
           FOR UPDATE;

        -- 2. Re-check the sender (data may have changed since the PENDING insert)
        IF NEW.sender_id IS NOT NULL THEN
            SELECT status, balance, remain_limit_week
              INTO v_s_status, v_s_balance, v_s_remain
              FROM wallets
             WHERE wallet_id = NEW.sender_id
               FOR UPDATE;

            IF v_s_status <> 'ACTIVE' THEN
                SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Sender wallet is locked';
            END IF;
            IF v_s_balance < NEW.amount THEN
                SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Insufficient balance';
            END IF;
            IF NEW.type = 'TRANSFER' AND v_s_remain < NEW.amount THEN
                SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Weekly transfer limit exceeded';
            END IF;
        END IF;

        -- 3. Re-check the receiver
        IF NEW.receiver_id IS NOT NULL THEN
            SELECT status INTO v_r_status
              FROM wallets
             WHERE wallet_id = NEW.receiver_id
               FOR UPDATE;

            IF v_r_status <> 'ACTIVE' THEN
                SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Receiver wallet is locked';
            END IF;
        END IF;

        -- 4. Apply the changes (allowed by the guard flag only here)
        SET @allow_balance_update = 1;

        IF NEW.sender_id IS NOT NULL THEN
            UPDATE wallets
               SET balance = balance - NEW.amount,
                   remain_limit_week = IF(NEW.type = 'TRANSFER',
                                          remain_limit_week - NEW.amount,
                                          remain_limit_week)
             WHERE wallet_id = NEW.sender_id;
        END IF;

        IF NEW.receiver_id IS NOT NULL THEN
            UPDATE wallets
               SET balance = balance + NEW.amount
             WHERE wallet_id = NEW.receiver_id;
        END IF;

        SET @allow_balance_update = 0;
    END IF;
END$$
DELIMITER ;


-- Validate_Transaction_Before_Insertion

DROP TRIGGER IF EXISTS trg_transactions_before_insert;
DELIMITER $$
CREATE TRIGGER trg_transactions_before_insert
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    DECLARE v_s_status   VARCHAR(10);
    DECLARE v_s_balance  DECIMAL(15, 2);
    DECLARE v_s_currency VARCHAR(3);
    DECLARE v_s_remain   DECIMAL(15, 2);
    DECLARE v_r_status   VARCHAR(10);
    DECLARE v_r_currency VARCHAR(3);
    DECLARE v_not_found  TINYINT DEFAULT 0;

    -- SELECT ... INTO khong co dong nao (vi khong ton tai) se sinh canh bao 1329 / SQLSTATE 02000.
    -- Mot so client (PyMySQL, Workbench...) hien canh bao do nhu LOI HE THONG va che mat thong bao
    -- that cua trigger. Handler nay nuot canh bao, de trigger tu SIGNAL dung thong bao.
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;

    -- amount must be greater than 0
    IF NEW.amount IS NULL OR NEW.amount <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Amount must be greater than 0';
    END IF;

    -- a new transaction must start as PENDING
    IF NEW.status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A new transaction must have status PENDING';
    END IF;

    -- type-specific sender/receiver rules
    IF NEW.type = 'DEPOSIT'
       AND (NEW.sender_id IS NOT NULL OR NEW.receiver_id IS NULL) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'DEPOSIT requires a receiver and no sender';
    END IF;

    IF NEW.type = 'WITHDRAW'
       AND (NEW.sender_id IS NULL OR NEW.receiver_id IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'WITHDRAW requires a sender and no receiver';
    END IF;

    IF NEW.type = 'TRANSFER'
       AND (NEW.sender_id IS NULL OR NEW.receiver_id IS NULL) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'TRANSFER requires both sender and receiver';
    END IF;

    IF NEW.type = 'TRANSFER' AND NEW.sender_id = NEW.receiver_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Sender and receiver cannot be the same wallet';
    END IF;

    -- sender wallet: exists, ACTIVE, enough balance
    IF NEW.sender_id IS NOT NULL THEN
        SELECT status, balance, currency, remain_limit_week
          INTO v_s_status, v_s_balance, v_s_currency, v_s_remain
          FROM wallets
         WHERE wallet_id = NEW.sender_id;

        IF v_s_status IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Sender wallet does not exist';
        END IF;
        IF v_s_status <> 'ACTIVE' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Sender wallet is locked';
        END IF;
        IF v_s_balance < NEW.amount THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Insufficient balance';
        END IF;
    END IF;

    -- receiver wallet: exists, ACTIVE
    IF NEW.receiver_id IS NOT NULL THEN
        SELECT status, currency
          INTO v_r_status, v_r_currency
          FROM wallets
         WHERE wallet_id = NEW.receiver_id;

        IF v_r_status IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Receiver wallet does not exist';
        END IF;
        IF v_r_status <> 'ACTIVE' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Receiver wallet is locked';
        END IF;
    END IF;

    -- transfer-only rules: same currency, remaining weekly limit
    IF NEW.type = 'TRANSFER' THEN
        IF v_s_currency <> v_r_currency THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Sender and receiver must use the same currency';
        END IF;
        IF NEW.amount > v_s_remain THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Weekly transfer limit exceeded';
        END IF;
    END IF;
END$$
DELIMITER ;