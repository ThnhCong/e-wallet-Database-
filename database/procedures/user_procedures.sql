USE ewallet;
DROP PROCEDURE IF EXISTS sp_user_create;
DROP PROCEDURE IF EXISTS sp_user_get_by_phone;
DROP PROCEDURE IF EXISTS sp_user_get_with_hash;
DROP PROCEDURE IF EXISTS sp_user_get_by_id;
DROP PROCEDURE IF EXISTS sp_user_update_profile;
DROP PROCEDURE IF EXISTS sp_user_update_password;
DELIMITER $$
CREATE PROCEDURE sp_user_create(IN p_user_name VARCHAR(100), IN p_password_hash VARCHAR(255), IN p_email VARCHAR(255), IN p_phone VARCHAR(20))
BEGIN
  INSERT INTO users(user_name,password_hash,email,phone) VALUES(p_user_name,p_password_hash,p_email,p_phone);
  SELECT LAST_INSERT_ID() AS user_id;
END$$
CREATE PROCEDURE sp_user_get_by_phone(IN p_phone VARCHAR(20))
BEGIN
  SELECT user_id,user_name,password_hash,email,phone FROM users WHERE phone=p_phone LIMIT 1;
END$$
CREATE PROCEDURE sp_user_get_with_hash(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT user_id,user_name,password_hash,email,phone FROM users WHERE user_id=p_user_id LIMIT 1;
END$$
CREATE PROCEDURE sp_user_get_by_id(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT user_id,user_name,email,phone FROM users WHERE user_id=p_user_id LIMIT 1;
END$$
CREATE PROCEDURE sp_user_update_profile(IN p_user_id BIGINT UNSIGNED, IN p_user_name VARCHAR(100), IN p_email VARCHAR(255), IN p_phone VARCHAR(20))
BEGIN
  UPDATE users SET user_name=p_user_name,email=p_email,phone=p_phone WHERE user_id=p_user_id;
  SELECT ROW_COUNT() AS affected_rows;
END$$
CREATE PROCEDURE sp_user_update_password(IN p_user_id BIGINT UNSIGNED, IN p_password_hash VARCHAR(255))
BEGIN
  UPDATE users SET password_hash=p_password_hash WHERE user_id=p_user_id;
  SELECT ROW_COUNT() AS affected_rows;
END$$
DELIMITER ;
