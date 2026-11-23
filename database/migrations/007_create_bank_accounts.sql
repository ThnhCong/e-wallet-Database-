USE ewallet;

-- =========================================================
-- 7. BANK_ACCOUNTS  (associative entity: Wallet N:M Bank)
--    One row = "this wallet is linked to this bank". The pair
--    (wallet_id, bank_id) is unique, so a wallet is linked to a bank at most once.
-- =========================================================
CREATE TABLE IF NOT EXISTS bank_accounts (
    bank_account_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    wallet_id BIGINT UNSIGNED NOT NULL,
    bank_id BIGINT UNSIGNED NOT NULL,
    status ENUM('PENDING', 'SUCCESS', 'FAIL') NOT NULL DEFAULT 'SUCCESS',
    linked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (bank_account_id),
    CONSTRAINT uq_bank_accounts_wallet_bank UNIQUE (wallet_id, bank_id),
    CONSTRAINT fk_bank_accounts_wallet_id FOREIGN KEY (wallet_id)
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_bank_accounts_bank_id FOREIGN KEY (bank_id)
        REFERENCES banks(bank_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

