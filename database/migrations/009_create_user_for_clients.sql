-- Application DB account used by the REST API (never by the GUI).
-- Change the password below, and the same value in config.json, before executing.
CREATE USER IF NOT EXISTS 'ewallet_app'@'%'
IDENTIFIED BY '514160';
ALTER USER 'ewallet_app'@'%'
IDENTIFIED BY '514160';

-- Remove all previously granted privileges
REVOKE ALL PRIVILEGES, GRANT OPTION
FROM 'ewallet_app'@'%';

-- Grant only what the application needs (no DELETE anywhere: history is permanent)
GRANT SELECT, INSERT, UPDATE ON ewallet.users         TO 'ewallet_app'@'%';
GRANT SELECT, INSERT, UPDATE ON ewallet.user_profiles TO 'ewallet_app'@'%';
GRANT SELECT, INSERT, UPDATE ON ewallet.wallets       TO 'ewallet_app'@'%';
GRANT SELECT, INSERT, UPDATE ON ewallet.transactions  TO 'ewallet_app'@'%';
GRANT SELECT                 ON ewallet.banks         TO 'ewallet_app'@'%';
GRANT SELECT, INSERT         ON ewallet.bank_accounts TO 'ewallet_app'@'%';
GRANT SELECT, INSERT         ON ewallet.audit_logs    TO 'ewallet_app'@'%';

-- Stored procedures
GRANT EXECUTE ON ewallet.* TO 'ewallet_app'@'%';

SHOW GRANTS FOR 'ewallet_app'@'%';
