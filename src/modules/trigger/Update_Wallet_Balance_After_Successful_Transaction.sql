USE ewallet;
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