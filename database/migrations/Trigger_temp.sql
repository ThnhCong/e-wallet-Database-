USE ewallet;

-- 1. Tạo lại user client chấp nhận kết nối từ mọi IP (%)
CREATE USER 'ewallet_client'@'%' IDENTIFIED BY 'Tina514160#';

-- 2. Cấp quyền SELECT, INSERT, UPDATE trên bảng users
GRANT SELECT, INSERT, UPDATE ON ewallet.users TO 'ewallet_client'@'%';

-- 3. Cấp quyền SELECT, INSERT, UPDATE trên bảng wallets
GRANT SELECT, INSERT, UPDATE ON ewallet.wallets TO 'ewallet_client'@'%';

-- 4. Áp dụng thay đổi ngay lập tức
FLUSH PRIVILEGES;