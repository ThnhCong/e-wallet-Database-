USE ewallet;

-- =========================================================
-- 7. BANK_ACCOUNTS  (associative entity: Wallet N:M Bank)
--    Each row records one link lifecycle. Generated unique keys enforce one active
--    link per wallet/bank and one active use of a bank account number; cancelled rows remain history.
-- =========================================================
CREATE TABLE IF NOT EXISTS bank_accounts (
    bank_account_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    wallet_id BIGINT UNSIGNED NOT NULL,
    bank_id BIGINT UNSIGNED NOT NULL,
    account_number VARCHAR(34) NOT NULL,
    status ENUM('PENDING', 'SUCCESS', 'FAIL', 'CANCELLED') NOT NULL DEFAULT 'SUCCESS',
    linked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active_wallet_id BIGINT UNSIGNED GENERATED ALWAYS AS (IF(status='SUCCESS', wallet_id, NULL)) STORED,
    active_bank_id BIGINT UNSIGNED GENERATED ALWAYS AS (IF(status='SUCCESS', bank_id, NULL)) STORED,
    active_account_number VARCHAR(34) GENERATED ALWAYS AS (IF(status='SUCCESS', account_number, NULL)) STORED,

    PRIMARY KEY (bank_account_id),
    CONSTRAINT uq_bank_accounts_active_wallet_bank UNIQUE (active_wallet_id, active_bank_id),
    CONSTRAINT uq_bank_accounts_active_account_number UNIQUE (active_bank_id, active_account_number),
    CONSTRAINT fk_bank_accounts_wallet_id FOREIGN KEY (wallet_id)
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_bank_accounts_bank_id FOREIGN KEY (bank_id)
        REFERENCES banks(bank_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

