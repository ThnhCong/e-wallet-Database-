-- 1. Tạo user
CREATE USER IF NOT EXISTS 'Tina514160'@'%' 
IDENTIFIED BY '514160';
ALTER USER 'Tina514160'@'%'
IDENTIFIED BY '514160';


-- 2. Xóa toàn bộ quyền đã cấp trước đó
REVOKE ALL PRIVILEGES, GRANT OPTION
FROM 'Tina514160'@'%';


-- 2. Cấp quyền CRUD cho table clients
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


-- 3. Kiểm tra quyền
SHOW GRANTS FOR 'Tina514160'@'%';
