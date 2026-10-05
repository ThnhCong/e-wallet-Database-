USE ewallet;
DROP EVENT   IF EXISTS ev_reset_weekly_limit;
DELIMITER $$
SET GLOBAL event_scheduler = ON;

CREATE EVENT ev_reset_weekly_limit
ON SCHEDULE EVERY 1 WEEK
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL (7 - WEEKDAY(CURRENT_DATE)) DAY)
DO
    UPDATE wallets SET remain_limit_week = limit_week;