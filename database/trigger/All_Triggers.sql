-- ============================================================
-- E-WALLET DATABASE TRIGGERS (MySQL 8.0+)
-- Run AFTER migrations/All_Migrations.sql and BEFORE procedures.
-- Financial balances are changed only when a PENDING transaction
-- becomes SUCCESS. All business history is append-only.
-- ============================================================
USE ewallet;

SET GLOBAL event_scheduler = ON;
DROP EVENT IF EXISTS ev_reset_weekly_limit;
DROP EVENT IF EXISTS ev_refresh_profile_age;
CREATE EVENT ev_refresh_profile_age
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL 1 DAY)
ON COMPLETION PRESERVE
ENABLE
DO UPDATE user_profiles
   SET age = TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE())
 WHERE age <> TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE());

CREATE EVENT ev_reset_weekly_limit
ON SCHEDULE EVERY 1 WEEK
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL (7 - WEEKDAY(CURRENT_DATE)) DAY)
ON COMPLETION PRESERVE
ENABLE
DO UPDATE wallets
   SET remain_limit_week = limit_week
 WHERE remain_limit_week <> limit_week;

-- ------------------------------------------------------------
-- Wallet defaults and balance protection
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_wallets_before_insert;
DROP TRIGGER IF EXISTS trg_wallets_before_update;
DROP TRIGGER IF EXISTS trg_wallets_before_delete;
DELIMITER $$
CREATE TRIGGER trg_wallets_before_insert
BEFORE INSERT ON wallets
FOR EACH ROW
BEGIN
    SET NEW.currency = UPPER(TRIM(NEW.currency));
    IF NEW.currency = 'VND' THEN
        SET NEW.limit_week = 10000000.00;
    ELSEIF NEW.currency = 'USD' THEN
        SET NEW.limit_week = 500.00;
    ELSE
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Unsupported currency: only VND and USD are supported';
    END IF;
    SET NEW.balance = 0.00;
    SET NEW.remain_limit_week = NEW.limit_week;
    SET NEW.status = 'ACTIVE';
END$$

CREATE TRIGGER trg_wallets_before_update
BEFORE UPDATE ON wallets
FOR EACH ROW
BEGIN
    IF NEW.balance < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Wallet balance cannot be negative';
    END IF;
    IF (NEW.balance <> OLD.balance OR NEW.remain_limit_week <> OLD.remain_limit_week)
       AND COALESCE(@allow_balance_update, 0) <> 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Wallet balance and weekly limit can only change through a successful transaction';
    END IF;
    IF NEW.user_id <> OLD.user_id OR NEW.currency <> OLD.currency
       OR NEW.limit_week <> OLD.limit_week OR NEW.created_at <> OLD.created_at THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Wallet ownership, currency, limit and creation time are immutable';
    END IF;
END$$

CREATE TRIGGER trg_wallets_before_delete
BEFORE DELETE ON wallets
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Wallet records cannot be deleted; lock the wallet instead';
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- User and profile records are retained; age is derived from DOB
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_users_before_delete;
DROP TRIGGER IF EXISTS trg_user_profiles_before_insert;
DROP TRIGGER IF EXISTS trg_user_profiles_before_update;
DROP TRIGGER IF EXISTS trg_user_profiles_before_delete;
DELIMITER $$
CREATE TRIGGER trg_users_before_delete
BEFORE DELETE ON users
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User records cannot be deleted';
END$$

CREATE TRIGGER trg_user_profiles_before_insert
BEFORE INSERT ON user_profiles
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth IS NULL OR NEW.date_of_birth >= CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Date of birth must be earlier than today';
    END IF;
    SET NEW.age = TIMESTAMPDIFF(YEAR, NEW.date_of_birth, CURDATE());
    IF NEW.age < 1 OR NEW.age > 120 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Date of birth must represent an age between 1 and 120';
    END IF;
END$$

CREATE TRIGGER trg_user_profiles_before_update
BEFORE UPDATE ON user_profiles
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth IS NULL OR NEW.date_of_birth >= CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Date of birth must be earlier than today';
    END IF;
    SET NEW.age = TIMESTAMPDIFF(YEAR, NEW.date_of_birth, CURDATE());
    IF NEW.age < 1 OR NEW.age > 120 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Date of birth must represent an age between 1 and 120';
    END IF;
    IF NEW.user_id <> OLD.user_id OR NEW.created_at <> OLD.created_at THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Profile owner and creation time are immutable';
    END IF;
END$$

CREATE TRIGGER trg_user_profiles_before_delete
BEFORE DELETE ON user_profiles
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User profiles cannot be deleted; update the profile instead';
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- Bank catalogue: never delete; only is_valid can be changed
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_banks_before_update;
DROP TRIGGER IF EXISTS trg_banks_before_delete;
DELIMITER $$
CREATE TRIGGER trg_banks_before_update
BEFORE UPDATE ON banks
FOR EACH ROW
BEGIN
    IF NEW.name <> OLD.name OR NEW.cooperated_at <> OLD.cooperated_at THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Bank identity is immutable; only is_valid can be updated';
    END IF;
END$$

CREATE TRIGGER trg_banks_before_delete
BEFORE DELETE ON banks
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Partner banks cannot be deleted; set is_valid=FALSE instead';
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- Bank account links: only SUCCESS -> CANCELLED is allowed
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_bank_accounts_before_insert;
DROP TRIGGER IF EXISTS trg_bank_accounts_before_update;
DROP TRIGGER IF EXISTS trg_bank_accounts_before_delete;
DELIMITER $$
CREATE TRIGGER trg_bank_accounts_before_insert
BEFORE INSERT ON bank_accounts
FOR EACH ROW
BEGIN
    DECLARE v_wallet_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_bank_valid BOOLEAN DEFAULT NULL;
    DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;

    SELECT status INTO v_wallet_status
      FROM wallets WHERE wallet_id = NEW.wallet_id;
    IF v_wallet_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Wallet does not exist';
    END IF;
    IF v_wallet_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Wallet is locked';
    END IF;

    SELECT is_valid INTO v_bank_valid
      FROM banks WHERE bank_id = NEW.bank_id;
    IF v_bank_valid IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Partner bank does not exist';
    END IF;
    IF v_bank_valid <> TRUE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Partner bank is not currently cooperating';
    END IF;

    IF NEW.account_number IS NULL OR NEW.account_number NOT REGEXP '^[0-9]{6,34}$' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank account number must contain 6-34 digits';
    END IF;
    IF NEW.status <> 'SUCCESS' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A new bank link must start as SUCCESS';
    END IF;
END$$

CREATE TRIGGER trg_bank_accounts_before_update
BEFORE UPDATE ON bank_accounts
FOR EACH ROW
BEGIN
    IF NEW.bank_account_id <> OLD.bank_account_id
       OR NEW.wallet_id <> OLD.wallet_id
       OR NEW.bank_id <> OLD.bank_id
       OR NEW.account_number <> OLD.account_number
       OR NEW.linked_at <> OLD.linked_at THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank link details are immutable';
    END IF;
    IF OLD.status <> 'SUCCESS' OR NEW.status <> 'CANCELLED' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only an active bank link can be cancelled';
    END IF;
END$$

CREATE TRIGGER trg_bank_accounts_before_delete
BEFORE DELETE ON bank_accounts
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Bank links cannot be deleted; cancel the link instead';
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- Transactions: immutable payload, only PENDING -> SUCCESS/FAIL
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_transactions_before_insert;
DROP TRIGGER IF EXISTS trg_transactions_before_update;
DROP TRIGGER IF EXISTS trg_transactions_after_update;
DROP TRIGGER IF EXISTS trg_transactions_before_delete;
DELIMITER $$
CREATE TRIGGER trg_transactions_before_insert
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    DECLARE v_sender_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_receiver_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_sender_balance DECIMAL(15,2) DEFAULT NULL;
    DECLARE v_sender_currency VARCHAR(3) DEFAULT NULL;
    DECLARE v_receiver_currency VARCHAR(3) DEFAULT NULL;
    DECLARE v_remaining DECIMAL(15,2) DEFAULT NULL;
    DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;

    IF NEW.amount IS NULL OR NEW.amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Amount must be greater than zero';
    END IF;
    IF NEW.status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A new transaction must start as PENDING';
    END IF;

    IF NEW.type = 'DEPOSIT' AND (NEW.sender_id IS NOT NULL OR NEW.receiver_id IS NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'DEPOSIT requires a receiver and no sender';
    ELSEIF NEW.type = 'WITHDRAW' AND (NEW.sender_id IS NULL OR NEW.receiver_id IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'WITHDRAW requires a sender and no receiver';
    ELSEIF NEW.type = 'TRANSFER' AND (NEW.sender_id IS NULL OR NEW.receiver_id IS NULL OR NEW.sender_id = NEW.receiver_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'TRANSFER requires two different wallets';
    END IF;

    IF NEW.sender_id IS NOT NULL THEN
        SELECT status, balance, currency, remain_limit_week
          INTO v_sender_status, v_sender_balance, v_sender_currency, v_remaining
          FROM wallets WHERE wallet_id = NEW.sender_id;
        IF v_sender_status IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sender wallet does not exist';
        END IF;
        IF v_sender_status <> 'ACTIVE' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sender wallet is locked';
        END IF;
        IF v_sender_balance < NEW.amount THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient balance';
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM bank_accounts ba
            INNER JOIN banks b ON b.bank_id = ba.bank_id
            WHERE ba.wallet_id = NEW.sender_id AND ba.status = 'SUCCESS' AND b.is_valid = TRUE
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sender wallet must be linked to an active partner bank';
        END IF;
    END IF;

    IF NEW.receiver_id IS NOT NULL THEN
        SELECT status, currency
          INTO v_receiver_status, v_receiver_currency
          FROM wallets WHERE wallet_id = NEW.receiver_id;
        IF v_receiver_status IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Receiver wallet does not exist';
        END IF;
        IF v_receiver_status <> 'ACTIVE' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Receiver wallet is locked';
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM bank_accounts ba
            INNER JOIN banks b ON b.bank_id = ba.bank_id
            WHERE ba.wallet_id = NEW.receiver_id AND ba.status = 'SUCCESS' AND b.is_valid = TRUE
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Receiver wallet must be linked to an active partner bank';
        END IF;
    END IF;

    IF NEW.type = 'TRANSFER' THEN
        IF v_sender_currency <> v_receiver_currency THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sender and receiver must use the same currency';
        END IF;
        IF NEW.amount > v_remaining THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Weekly transfer limit exceeded';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_transactions_before_update
BEFORE UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF OLD.status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Completed transactions cannot be modified';
    END IF;
    IF NEW.status NOT IN ('SUCCESS', 'FAIL') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A PENDING transaction can only become SUCCESS or FAIL';
    END IF;
    IF NEW.type <> OLD.type OR NEW.amount <> OLD.amount
       OR NOT (NEW.sender_id <=> OLD.sender_id)
       OR NOT (NEW.receiver_id <=> OLD.receiver_id)
       OR NEW.created_at <> OLD.created_at THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only transaction status can be changed';
    END IF;
END$$

CREATE TRIGGER trg_transactions_after_update
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
    DECLARE v_lock_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_sender_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_sender_balance DECIMAL(15,2) DEFAULT NULL;
    DECLARE v_sender_remaining DECIMAL(15,2) DEFAULT NULL;
    DECLARE v_receiver_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_bank_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_bank_id = NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET @allow_balance_update = 0;
        RESIGNAL;
    END;

    IF OLD.status = 'PENDING' AND NEW.status = 'SUCCESS' THEN
        -- Lock all participating wallets in ascending ID order.
        SET v_lock_id = LEAST(COALESCE(NEW.sender_id, NEW.receiver_id), COALESCE(NEW.receiver_id, NEW.sender_id));
        SELECT wallet_id INTO v_lock_id FROM wallets WHERE wallet_id = v_lock_id FOR UPDATE;
        SET v_lock_id = GREATEST(COALESCE(NEW.sender_id, NEW.receiver_id), COALESCE(NEW.receiver_id, NEW.sender_id));
        SELECT wallet_id INTO v_lock_id FROM wallets WHERE wallet_id = v_lock_id FOR UPDATE;

        IF NEW.sender_id IS NOT NULL THEN
            SELECT status, balance, remain_limit_week
              INTO v_sender_status, v_sender_balance, v_sender_remaining
              FROM wallets WHERE wallet_id = NEW.sender_id FOR UPDATE;
            IF v_sender_status <> 'ACTIVE' THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sender wallet is locked';
            END IF;
            IF v_sender_balance < NEW.amount THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient balance';
            END IF;
            IF NEW.type = 'TRANSFER' AND v_sender_remaining < NEW.amount THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Weekly transfer limit exceeded';
            END IF;
            -- Lock and re-check a cooperating bank at settlement time.
            SET v_bank_id = NULL;
            SELECT b.bank_id INTO v_bank_id
              FROM bank_accounts ba INNER JOIN banks b ON b.bank_id = ba.bank_id
             WHERE ba.wallet_id = NEW.sender_id AND ba.status = 'SUCCESS' AND b.is_valid = TRUE
             ORDER BY ba.bank_account_id LIMIT 1 FOR UPDATE;
            IF v_bank_id IS NULL THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sender wallet has no active partner bank link';
            END IF;
        END IF;

        IF NEW.receiver_id IS NOT NULL THEN
            SELECT status INTO v_receiver_status FROM wallets WHERE wallet_id = NEW.receiver_id FOR UPDATE;
            IF v_receiver_status <> 'ACTIVE' THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Receiver wallet is locked';
            END IF;
            SET v_bank_id = NULL;
            SELECT b.bank_id INTO v_bank_id
              FROM bank_accounts ba INNER JOIN banks b ON b.bank_id = ba.bank_id
             WHERE ba.wallet_id = NEW.receiver_id AND ba.status = 'SUCCESS' AND b.is_valid = TRUE
             ORDER BY ba.bank_account_id LIMIT 1 FOR UPDATE;
            IF v_bank_id IS NULL THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Receiver wallet has no active partner bank link';
            END IF;
        END IF;

        SET @allow_balance_update = 1;
        IF NEW.sender_id IS NOT NULL THEN
            UPDATE wallets
               SET balance = balance - NEW.amount,
                   remain_limit_week = IF(NEW.type = 'TRANSFER', remain_limit_week - NEW.amount, remain_limit_week)
             WHERE wallet_id = NEW.sender_id;
        END IF;
        IF NEW.receiver_id IS NOT NULL THEN
            UPDATE wallets SET balance = balance + NEW.amount WHERE wallet_id = NEW.receiver_id;
        END IF;
        SET @allow_balance_update = 0;
    END IF;
END$$

CREATE TRIGGER trg_transactions_before_delete
BEFORE DELETE ON transactions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transaction history cannot be deleted';
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- Audit logs are immutable and append-only
-- ------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_audit_logs_before_update;
DROP TRIGGER IF EXISTS trg_audit_logs_before_delete;
DELIMITER $$
CREATE TRIGGER trg_audit_logs_before_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit logs cannot be modified';
END$$
CREATE TRIGGER trg_audit_logs_before_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit logs cannot be deleted';
END$$
DELIMITER ;
