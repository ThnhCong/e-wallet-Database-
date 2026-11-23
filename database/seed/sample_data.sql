-- =====================================================================
-- SAMPLE DATA for demonstration (valid cases).  Run AFTER migrations, triggers, procedures.
-- All sample users have the password  123456  (stored as legacy SHA-256; the application
-- upgrades it to PBKDF2 at the first login).  0777777777 is the administrator in config.json.
-- =====================================================================
USE ewallet;

-- Partner banks (system data, managed by the database administrator)
INSERT INTO banks(name, cooperated_at) VALUES
 ('Vietcombank', '2024-01-15'), ('BIDV', '2024-03-01'), ('Techcombank', '2024-06-20'),
 ('ACB', '2025-02-10'), ('MB Bank', '2025-09-05');

-- Users
INSERT INTO users(user_name, password_hash, email, phone) VALUES
 ('System Admin', SHA2('123456',256), 'admin@ewallet.vn', '0777777777'),
 ('Nguyen Van An', SHA2('123456',256), 'an@example.com',   '0901000001'),
 ('Tran Thi Binh', SHA2('123456',256), 'binh@example.com',  '0901000002'),
 ('Le Van Cuong',  SHA2('123456',256), 'cuong@example.com', '0901000003');

-- Wallets (limit_week / remain_limit_week are filled by the trigger from the currency)
INSERT INTO wallets(user_id, currency) VALUES
 (2,'VND'), (2,'USD'),      -- wallet 1, 2 : An
 (3,'VND'),                 -- wallet 3    : Binh
 (4,'VND'), (4,'USD');      -- wallet 4, 5 : Cuong

-- Profiles: only An and Binh have chosen "update information" (Cuong has none: 1:0..1)
INSERT INTO user_profiles(user_id, age, sex, address, job, country) VALUES
 (2, 28, 'MALE',   '12 Nguyen Hue, Ho Chi Minh City', 'Software engineer', 'Vietnam'),
 (3, 34, 'FEMALE', '5 Tran Phu, Da Nang',             'Accountant',        'Vietnam');

-- Bank links (Wallet N:M Bank through bank_accounts; status defaults to SUCCESS)
INSERT INTO bank_accounts(wallet_id, bank_id) VALUES
 (1,1), (1,2),              -- An's VND wallet: Vietcombank + BIDV
 (3,1),                     -- Binh's wallet : Vietcombank
 (4,3);                     -- Cuong's wallet: Techcombank

-- Transactions: every one is inserted as PENDING and then set to SUCCESS;
-- the AFTER UPDATE trigger moves the money (the application does exactly the same).
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL, 1, 'DEPOSIT', 5000000);
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=1;
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL, 2, 'DEPOSIT', 300);
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=2;
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL, 3, 'DEPOSIT', 2000000);
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=3;
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (1, 3, 'TRANSFER', 1000000);
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=4;
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (3, NULL, 'WITHDRAW', 500000);
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=5;

-- Audit trail of the sample actions (normally written by the Application Layer)
INSERT INTO audit_logs(user_id, wallet_id, transaction_id, action) VALUES
 (2,NULL,NULL,'REGISTER'), (2,1,NULL,'CREATE_WALLET'), (2,1,NULL,'LINK_BANK'),
 (2,1,4,'TRANSFER'), (3,3,4,'TRANSFER_RECEIVED'), (3,3,5,'WITHDRAW');

SELECT wallet_id, user_id, currency, balance, limit_week, remain_limit_week, status FROM wallets;
