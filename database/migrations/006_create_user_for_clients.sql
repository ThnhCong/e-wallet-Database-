-- Replace CHANGE_ME_BEFORE_EXECUTING with the password stored in config.json before execution.
-- 1. Create application DB user
CREATE USER IF NOT EXISTS 'ewallet_app'@'%' 
IDENTIFIED BY '514160';
ALTER USER 'ewallet_app'@'%'
IDENTIFIED BY '514160';

-- 2. Remove all previously granted permissions
REVOKE ALL PRIVILEGES, GRANT OPTION
FROM 'ewallet_app'@'%';

-- 3. Grant only the required table privileges to the application account
GRANT SELECT, INSERT, UPDATE
ON ewallet.users
TO 'ewallet_app'@'%';

GRANT SELECT, INSERT, UPDATE
ON ewallet.wallets
TO 'ewallet_app'@'%';

GRANT SELECT, INSERT, UPDATE
ON ewallet.transactions
TO 'ewallet_app'@'%';

GRANT SELECT, INSERT
ON ewallet.audit_logs
TO 'ewallet_app'@'%';

GRANT EXECUTE ON ewallet.* TO 'ewallet_app'@'%';

-- 4. ReCheck these granted permissions
SHOW GRANTS FOR 'ewallet_app'@'%';
