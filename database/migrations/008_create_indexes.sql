USE ewallet;

-- =========================================================
-- 8. CREATE INDEXES
-- Additional indexes for frequently queried columns
-- =========================================================

-- WALLETS
CREATE INDEX idx_wallets_status
    ON wallets(status);
    
CREATE INDEX idx_wallets_user_id 
    ON wallets(user_id);
    
CREATE INDEX idx_wallets_currency
	ON wallets(currency);

-- TRANSACTIONS
CREATE INDEX idx_transactions_sender_id
    ON transactions(sender_id);

CREATE INDEX idx_transactions_receiver_id
    ON transactions(receiver_id);

CREATE INDEX idx_transactions_type
    ON transactions(type);

CREATE INDEX idx_transactions_status
    ON transactions(status);

CREATE INDEX idx_transactions_created_at
    ON transactions(created_at);

-- AUDIT LOGS
CREATE INDEX idx_audit_logs_user_id
    ON audit_logs(user_id);

CREATE INDEX idx_audit_logs_wallet_id
    ON audit_logs(wallet_id);

CREATE INDEX idx_audit_logs_transaction_id
    ON audit_logs(transaction_id);

CREATE INDEX idx_audit_logs_created_at
    ON audit_logs(created_at);

-- USER_PROFILES: user_id is already indexed by uq_user_profiles_user_id

-- BANK_ACCOUNTS: wallet_id is the left-most column of uq_bank_accounts_wallet_bank
CREATE INDEX idx_bank_accounts_bank_id
    ON bank_accounts(bank_id);

CREATE INDEX idx_bank_accounts_status
    ON bank_accounts(status);
