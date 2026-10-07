USE ewallet;

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
