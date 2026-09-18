USE ewallet;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    sender_id BIGINT UNSIGNED NULL,

    receiver_id BIGINT UNSIGNED NULL,

    type ENUM(
        'DEPOSIT',
        'TRANSFER',
        'WITHDRAW'
    ) NOT NULL,

    amount DECIMAL(19,2) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    status ENUM(
        'PENDING',
        'SUCCESS',
        'FAIL'
    ) NOT NULL DEFAULT 'PENDING',

    PRIMARY KEY (transaction_id),

    CONSTRAINT chk_transactions_amount
        CHECK (amount > 0),

    CONSTRAINT fk_transactions_sender
        FOREIGN KEY (sender_id)
        REFERENCES wallets(wallet_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_transactions_receiver
        FOREIGN KEY (receiver_id)
        REFERENCES wallets(wallet_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
