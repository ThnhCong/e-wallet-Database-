USE ewallet;

-- =========================================================
-- 5. USER_PROFILES  (1:1 with users, optional: created only when the user
--    chooses to save personal information. No row exists before that action.
--    created_at records the first successful save time and is never reset on update)
-- =========================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    user_profile_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    date_of_birth DATE NOT NULL,
    age TINYINT UNSIGNED NOT NULL,
    sex ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL,
    address VARCHAR(255) NOT NULL,
    job VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_profile_id),
    CONSTRAINT uq_user_profiles_user_id UNIQUE (user_id),
    CONSTRAINT fk_user_profiles_user_id FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_user_profiles_age CHECK (age BETWEEN 1 AND 120)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

