USE ewallet;
-- LOI CU: file cu co "DELIMITER $$" nhung khong ket thuc bang $$ -> lenh CREATE EVENT khong bao gio
-- duoc thuc thi => event KHONG ton tai. Event nay khong can DELIMITER (chi 1 cau lenh).
SET GLOBAL event_scheduler = ON;
DROP EVENT IF EXISTS ev_reset_weekly_limit;
CREATE EVENT ev_reset_weekly_limit
ON SCHEDULE EVERY 1 WEEK
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL (7 - WEEKDAY(CURRENT_DATE)) DAY)   -- thu Hai ke tiep 00:00
ON COMPLETION PRESERVE
ENABLE
DO
    UPDATE wallets SET remain_limit_week = limit_week WHERE remain_limit_week <> limit_week;