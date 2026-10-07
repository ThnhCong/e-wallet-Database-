USE ewallet;

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