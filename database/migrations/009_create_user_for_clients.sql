-- Run as a MySQL administrator AFTER All_Procedures.sql.
-- The API account can execute approved routines only. It has no direct
-- SELECT/INSERT/UPDATE/DELETE privilege on tables.
CREATE USER IF NOT EXISTS 'ewallet_app'@'%' IDENTIFIED BY '514160';
ALTER USER 'ewallet_app'@'%' IDENTIFIED BY '514160';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'ewallet_app'@'%';
GRANT EXECUTE ON ewallet.* TO 'ewallet_app'@'%';
SHOW GRANTS FOR 'ewallet_app'@'%';
