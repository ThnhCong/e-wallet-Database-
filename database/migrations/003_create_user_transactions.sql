USE ewallet;

-- 3. TRANSACTIONS
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    sender_id BIGINT UNSIGNED NULL,
    receiver_id BIGINT UNSIGNED NULL,
    type ENUM('DEPOSIT', 'TRANSFER', 'WITHDRAW') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status ENUM('PENDING', 'SUCCESS', 'FAIL') NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (transaction_id),
    CONSTRAINT fk_transactions_sender_id FOREIGN KEY (sender_id) 
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_transactions_receiver_id FOREIGN KEY (receiver_id) 
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_transactions_amount CHECK (amount > 0)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;