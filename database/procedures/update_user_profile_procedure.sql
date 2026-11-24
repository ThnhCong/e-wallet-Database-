-- Replace the user-profile procedures on an existing ewallet database.
USE ewallet;
SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- Normalize the database default and the two tables participating in profile search.
-- This is safe for existing rows; it converts their text columns to the project collation.
ALTER DATABASE ewallet CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE user_profiles CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

DROP PROCEDURE IF EXISTS sp_user_profile_get;
DROP PROCEDURE IF EXISTS sp_user_profile_save;
DROP PROCEDURE IF EXISTS sp_admin_list_user_profiles;
DELIMITER $$
CREATE PROCEDURE sp_user_profile_get(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT user_profile_id,user_id,date_of_birth,age,sex,address,job,country,created_at
  FROM user_profiles WHERE user_id=p_user_id LIMIT 1;
END$$
CREATE PROCEDURE sp_user_profile_save(IN p_user_id BIGINT UNSIGNED, IN p_date_of_birth DATE, IN p_age TINYINT UNSIGNED, IN p_sex VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
                                      IN p_address VARCHAR(255), IN p_job VARCHAR(100), IN p_country VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci)
BEGIN
  DECLARE v_rows INT DEFAULT 0;
  -- created_at is set only when the profile is first inserted.
  -- On duplicate key (profile already exists), it is deliberately preserved.
  INSERT INTO user_profiles(user_id,date_of_birth,age,sex,address,job,country,created_at)
  VALUES(p_user_id,p_date_of_birth,p_age,p_sex,p_address,p_job,p_country,CURRENT_TIMESTAMP)
  ON DUPLICATE KEY UPDATE
      date_of_birth=VALUES(date_of_birth),
      age=VALUES(age),
      sex=VALUES(sex),
      address=VALUES(address),
      job=VALUES(job),
      country=VALUES(country);
  SET v_rows = ROW_COUNT();
  SELECT user_profile_id, (v_rows = 1) AS created FROM user_profiles WHERE user_id=p_user_id;
END$$
-- Admin listing always returns one result row, even when there are no profiles
-- or the requested page is outside the current range. In that case the profile
-- columns are NULL and total_count still contains the real filtered count.
CREATE PROCEDURE sp_admin_list_user_profiles(
    IN p_search VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, IN p_sex VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, IN p_country VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
    IN p_sort_by VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, IN p_sort_order VARCHAR(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
    IN p_limit INT, IN p_offset INT
)
BEGIN
    SELECT page_rows.user_profile_id,
           page_rows.user_id,
           page_rows.user_name,
           page_rows.email,
           page_rows.phone,
           page_rows.date_of_birth,
           page_rows.age,
           page_rows.sex,
           page_rows.address,
           page_rows.job,
           page_rows.country,
           page_rows.created_at,
           totals.total_count
    FROM (
        SELECT COUNT(*) AS total_count
        FROM user_profiles p
        INNER JOIN users u ON u.user_id = p.user_id
        WHERE (p_search IS NULL
               OR (CAST(p.user_id AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.user_name COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.email COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.address COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.job COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci))
          AND (p_sex IS NULL OR (p.sex COLLATE utf8mb4_0900_ai_ci) = (p_sex COLLATE utf8mb4_0900_ai_ci))
          AND (p_country IS NULL OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_country, '%') COLLATE utf8mb4_0900_ai_ci))
    ) AS totals
    LEFT JOIN (
        SELECT p.user_profile_id, p.user_id, u.user_name, u.email, u.phone,
               p.date_of_birth, p.age, p.sex, p.address, p.job, p.country, p.created_at
        FROM user_profiles p
        INNER JOIN users u ON u.user_id = p.user_id
        WHERE (p_search IS NULL
               OR (CAST(p.user_id AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.user_name COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (u.email COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.address COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.job COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci)
               OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_search, '%') COLLATE utf8mb4_0900_ai_ci))
          AND (p_sex IS NULL OR (p.sex COLLATE utf8mb4_0900_ai_ci) = (p_sex COLLATE utf8mb4_0900_ai_ci))
          AND (p_country IS NULL OR (p.country COLLATE utf8mb4_0900_ai_ci) LIKE (CONCAT('%', p_country, '%') COLLATE utf8mb4_0900_ai_ci))
        ORDER BY
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('created_at' COLLATE utf8mb4_0900_ai_ci) AND p.created_at IS NULL THEN 1 ELSE 0 END ASC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('created_at' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('ASC' COLLATE utf8mb4_0900_ai_ci) THEN p.created_at END ASC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('created_at' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('DESC' COLLATE utf8mb4_0900_ai_ci) THEN p.created_at END DESC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('user_id' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('ASC' COLLATE utf8mb4_0900_ai_ci) THEN p.user_id END ASC,
            CASE WHEN (p_sort_by COLLATE utf8mb4_0900_ai_ci) = ('user_id' COLLATE utf8mb4_0900_ai_ci) AND (p_sort_order COLLATE utf8mb4_0900_ai_ci) = ('DESC' COLLATE utf8mb4_0900_ai_ci) THEN p.user_id END DESC,
            p.user_profile_id DESC
        LIMIT p_limit OFFSET p_offset
    ) AS page_rows ON TRUE;
END$$
DELIMITER ;
