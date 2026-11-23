USE ewallet;

-- =========================================================
-- 6. BANKS  (partner banks of the system)
-- =========================================================
CREATE TABLE IF NOT EXISTS banks (
    bank_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    cooperated_at DATE NOT NULL DEFAULT (CURRENT_DATE),

    PRIMARY KEY (bank_id),
    CONSTRAINT uq_banks_name UNIQUE (name)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

