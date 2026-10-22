-- 1. Create user
CREATE USER IF NOT EXISTS 'Tina514160'@'%' 
IDENTIFIED BY '514160';
ALTER USER 'Tina514160'@'%'
IDENTIFIED BY '514160';

-- 2. Remove all previously granted permissions
REVOKE ALL PRIVILEGES, GRANT OPTION
FROM 'Tina514160'@'%';

-- 3. Grant CRUD for table clients
GRANT SELECT, INSERT, UPDATE
ON ewallet.users
TO 'Tina514160'@'%';

GRANT SELECT, INSERT, UPDATE
ON ewallet.wallets
TO 'Tina514160'@'%';

GRANT SELECT, INSERT, UPDATE
ON ewallet.transactions
TO 'Tina514160'@'%';

GRANT SELECT, INSERT
ON ewallet.audit_logs
TO 'Tina514160'@'%';

-- 4. ReCheck these granted permissions
SHOW GRANTS FOR 'Tina514160'@'%';
