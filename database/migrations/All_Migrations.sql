-- =========================================================
-- Create Database
-- MySQL 8.0: use one collation consistently throughout the project.
-- =========================================================
SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE DATABASE IF NOT EXISTS ewallet
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
ALTER DATABASE ewallet CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
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
    PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_phone UNIQUE (phone),
    CONSTRAINT chk_users_email CHECK (email LIKE '%@%.%')
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
 
-- =========================================================
-- 2. WALLETS
-- =========================================================
CREATE TABLE IF NOT EXISTS wallets (
    wallet_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'VND',
    limit_week DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    remain_limit_week DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    status ENUM('ACTIVE', 'LOCKED') NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 
    PRIMARY KEY (wallet_id),
    CONSTRAINT fk_wallets_user_id FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_wallets_balance CHECK (balance >= 0),
    CONSTRAINT chk_wallets_currency CHECK (currency IN ('VND', 'USD')),
    CONSTRAINT chk_wallets_limit_week CHECK (limit_week >= 0),
    CONSTRAINT chk_wallets_remain_limit_week
	CHECK (
		remain_limit_week >= 0
		AND remain_limit_week <= limit_week
	)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
 
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
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_transactions_receiver_id FOREIGN KEY (receiver_id)
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_transactions_amount CHECK (amount > 0),
    CONSTRAINT chk_transactions_shape CHECK (
        (type = 'DEPOSIT' AND sender_id IS NULL AND receiver_id IS NOT NULL) OR
        (type = 'WITHDRAW' AND sender_id IS NOT NULL AND receiver_id IS NULL) OR
        (type = 'TRANSFER' AND sender_id IS NOT NULL AND receiver_id IS NOT NULL AND sender_id <> receiver_id)
    )
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
 
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
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_audit_logs_transaction_id FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_audit_logs_action CHECK (action IN (
        'REGISTER', 'LOGIN', 'LOGOUT', 'CHANGE_PASSWORD', 'UPDATE_PROFILE',
        'CREATE_WALLET', 'LOCK_WALLET', 'UNLOCK_WALLET',
        'DEPOSIT', 'WITHDRAW', 'TRANSFER', 'TRANSFER_RECEIVED',
        'LINK_BANK', 'UNLINK_BANK'))
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
 

-- =========================================================
-- 5. USER_PROFILES  (1:1 with users, optional: created only when the user
--    chooses to save personal information. No row exists before that action.
--    created_at records the first successful save time and is never reset on update)
-- =========================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    user_profile_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    date_of_birth DATE NOT NULL,
    age TINYINT UNSIGNED NOT NULL,
    sex ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL,
    address VARCHAR(255) NOT NULL,
    job VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_profile_id),
    CONSTRAINT uq_user_profiles_user_id UNIQUE (user_id),
    CONSTRAINT fk_user_profiles_user_id FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_user_profiles_age CHECK (age BETWEEN 1 AND 120)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- =========================================================
-- 6. BANKS  (partner banks of the system)
-- =========================================================
CREATE TABLE IF NOT EXISTS banks (
    bank_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    cooperated_at DATE NOT NULL DEFAULT (CURRENT_DATE),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (bank_id),
    CONSTRAINT uq_banks_name UNIQUE (name),
    CONSTRAINT chk_banks_is_valid CHECK (is_valid IN (0, 1))
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

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
    CONSTRAINT chk_bank_accounts_account_number CHECK (account_number REGEXP '^[0-9]{6,34}$'),
    CONSTRAINT fk_bank_accounts_wallet_id FOREIGN KEY (wallet_id)
        REFERENCES wallets(wallet_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_bank_accounts_bank_id FOREIGN KEY (bank_id)
        REFERENCES banks(bank_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

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


-- Composite indexes for common API access patterns
CREATE INDEX idx_transactions_sender_created ON transactions(sender_id, created_at DESC);
CREATE INDEX idx_transactions_receiver_created ON transactions(receiver_id, created_at DESC);
CREATE INDEX idx_bank_accounts_wallet_status ON bank_accounts(wallet_id, status, bank_id);
CREATE INDEX idx_user_profiles_country_sex ON user_profiles(country, sex);
