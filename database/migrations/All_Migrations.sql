-- =========================================================
-- Create Database
-- =========================================================
CREATE DATABASE IF NOT EXISTS ewallet
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE ewallet;
 
-- =========================================================
-- 1. USERS
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    user_role VARCHAR(20) NOT NULL DEFAULT 'user',
    PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_phone UNIQUE (phone),
    CONSTRAINT chk_users_email CHECK (email LIKE '%@%.%'),
    CONSTRAINT chk_users_user_role CHECK (user_role IN ('user', 'admin'))
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
 
-- =========================================================
-- 2. WALLETS
-- =========================================================
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
 
-- =========================================================
-- 3. TRANSACTIONS
-- =========================================================
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
        'DEPOSIT', 'WITHDRAW', 'TRANSFER', 'TRANSFER_RECEIVED'))
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
 

-- =========================================================
-- 5. CREATE INDEXES
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

-- =========================================================
-- 6. CREATE USER FOR CLIENTS
-- =========================================================
-- 1. Create user
CREATE USER IF NOT EXISTS 'Tina514160'@'%' 
IDENTIFIED BY '514160';
ALTER USER 'Tina514160'@'%'
IDENTIFIED BY '514160';

-- 2. Remove all previously granted permissions
REVOKE ALL PRIVILEGES, GRANT OPTION
FROM 'Tina514160'@'%';

-- 3. Grant CRUD for table clients
GRANT SELECT, INSERT, UPDATE
ON ewallet.users
TO 'Tina514160'@'%';

GRANT SELECT, INSERT, UPDATE
ON ewallet.wallets
TO 'Tina514160'@'%';

GRANT SELECT, INSERT, UPDATE
ON ewallet.transactions
TO 'Tina514160'@'%';

GRANT SELECT, INSERT
ON ewallet.audit_logs
TO 'Tina514160'@'%';

-- 4. ReCheck these granted permissions
SHOW GRANTS FOR 'Tina514160'@'%';
