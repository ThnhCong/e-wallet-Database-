USE ewallet;
DROP PROCEDURE IF EXISTS sp_admin_list_users;
DELIMITER $$
CREATE PROCEDURE sp_admin_list_users(IN p_limit INT)
BEGIN
  SELECT u.user_id,u.user_name,u.email,u.phone,COUNT(w.wallet_id) AS wallet_count,
         EXISTS(SELECT 1 FROM user_profiles p WHERE p.user_id=u.user_id) AS has_profile
  FROM users u LEFT JOIN wallets w ON w.user_id=u.user_id
  GROUP BY u.user_id,u.user_name,u.email,u.phone
  ORDER BY u.user_id LIMIT p_limit;
END$$
DELIMITER ;
