USE ewallet;
CREATE TABLE IF NOT EXISTS ledgers (
    ledger_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    wallet_id BIGINT UNSIGNED NOT NULL,

    transaction_id BIGINT UNSIGNED NOT NULL,

    type ENUM(
        'DEBIT',
        'CREDIT'
    ) NOT NULL,

    amount DECIMAL(19,2) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (ledger_id),

    CONSTRAINT chk_ledgers_amount
        CHECK (amount > 0),

    CONSTRAINT fk_ledgers_wallet
        FOREIGN KEY (wallet_id)
        REFERENCES wallets(wallet_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_ledgers_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
