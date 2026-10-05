-- 1. Xóa user 'clients' cũ (nếu tồn tại)
DROP USER IF EXISTS 'clients'@'%';

-- Nếu trước đó bạn đã tạo user kết nối từ localhost, hãy xóa thêm dòng này:
-- DROP USER IF EXISTS 'clients'@'localhost';

-- 2. Tạo lại user 'clients' mới
CREATE USER 'Cong'@'%' IDENTIFIED BY '141106';

-- 3. Cấp quyền SELECT và INSERT trên TOÀN BỘ các bảng trong ewallet
GRANT SELECT, INSERT ON ewallet.* TO 'Cong'@'%';

-- 4. Cấp quyền UPDATE CHỈ TRÊN 2 bảng 'wallets' và 'users'
GRANT UPDATE ON ewallet.wallets TO 'Cong'@'%';
GRANT UPDATE ON ewallet.users TO 'Cong'@'%';

-- 5. Cập nhật hệ thống phân quyền
FLUSH PRIVILEGES;