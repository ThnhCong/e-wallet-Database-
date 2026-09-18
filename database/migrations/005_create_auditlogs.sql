USE ewallet;
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_log_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    transaction_id BIGINT UNSIGNED NULL,

    wallet_id BIGINT UNSIGNED NULL,

    user_id BIGINT UNSIGNED NOT NULL,

    action VARCHAR(100) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (audit_log_id),

    CONSTRAINT fk_audit_logs_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_audit_logs_wallet
        FOREIGN KEY (wallet_id)
        REFERENCES wallets(wallet_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
