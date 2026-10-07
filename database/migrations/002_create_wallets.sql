USE ewallet;
-- 2. WALLETS
CREATE TABLE IF NOT EXISTS wallets (
    wallet_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'VND',
    limit_week DECIMAL(15, 2) NOT NULL,
    remain_limit_week DECIMAL(15, 2) NOT NULL,
    status ENUM('ACTIVE', 'LOCKED') NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (wallet_id),
    CONSTRAINT fk_wallets_user_id FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_wallets_balance CHECK (balance >= 0),
    CONSTRAINT chk_wallets_limit_week CHECK (limit_week >= 0),
    CONSTRAINT chk_wallets_remain_limit_week
		CHECK (
			remain_limit_week >= 0
			AND remain_limit_week <= limit_week
		)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;