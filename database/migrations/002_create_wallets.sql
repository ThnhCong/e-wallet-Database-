USE ewallet;
CREATE TABLE IF NOT EXISTS wallets (
    wallet_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    user_id BIGINT UNSIGNED NOT NULL,

    balance DECIMAL(19,2) NOT NULL DEFAULT 0.00,

    currency VARCHAR(10) NOT NULL DEFAULT 'VND',

    limit_week DECIMAL(19,2) NOT NULL DEFAULT 10000000.00,

    PRIMARY KEY (wallet_id),

    CONSTRAINT uq_wallets_user
        UNIQUE (user_id),

    CONSTRAINT chk_wallets_balance
        CHECK (balance >= 0),

    CONSTRAINT chk_wallets_limit_week
        CHECK (limit_week >= 0),

    CONSTRAINT fk_wallets_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
