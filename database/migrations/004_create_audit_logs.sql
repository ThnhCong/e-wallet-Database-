USE ewallet;

-- =========================================================
-- 4. AUDIT LOGS
-- =========================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_log_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    wallet_id BIGINT UNSIGNED NULL,
    transaction_id BIGINT UNSIGNED NULL,
    action VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
    PRIMARY KEY (audit_log_id),
    CONSTRAINT fk_audit_logs_user_id FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_audit_logs_wallet_id FOREIGN KEY (wallet_id)
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_audit_logs_transaction_id FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_audit_logs_action CHECK (action IN (
        'REGISTER', 'LOGIN', 'LOGOUT', 'CHANGE_PASSWORD', 'UPDATE_PROFILE',
        'CREATE_WALLET', 'LOCK_WALLET', 'UNLOCK_WALLET',
        'DEPOSIT', 'WITHDRAW', 'TRANSFER', 'TRANSFER_RECEIVED',
        'LINK_BANK', 'UNLINK_BANK'))
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
 

