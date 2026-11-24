USE ewallet;
-- Age is derived from date_of_birth in the database.
DROP TRIGGER IF EXISTS trg_user_profiles_before_insert;
DROP TRIGGER IF EXISTS trg_user_profiles_before_update;
DELIMITER $$
CREATE TRIGGER trg_user_profiles_before_insert BEFORE INSERT ON user_profiles FOR EACH ROW
BEGIN
 IF NEW.date_of_birth IS NULL OR NEW.date_of_birth>=CURDATE() THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth must be earlier than today'; END IF;
 SET NEW.age=TIMESTAMPDIFF(YEAR,NEW.date_of_birth,CURDATE());
 IF NEW.age<1 OR NEW.age>120 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth must represent an age between 1 and 120'; END IF;
END$$
CREATE TRIGGER trg_user_profiles_before_update BEFORE UPDATE ON user_profiles FOR EACH ROW
BEGIN
 IF NEW.date_of_birth IS NULL OR NEW.date_of_birth>=CURDATE() THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth must be earlier than today'; END IF;
 SET NEW.age=TIMESTAMPDIFF(YEAR,NEW.date_of_birth,CURDATE());
 IF NEW.age<1 OR NEW.age>120 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Date of birth must represent an age between 1 and 120'; END IF;
END$$
DELIMITER ;
