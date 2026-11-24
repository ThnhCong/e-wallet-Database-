-- ============================================================
-- DEMONSTRATION DATA - run only on a fresh database.
-- All demo users use password 123456 (legacy SHA-256; app upgrades on login).
-- Admin phone is configured in config.json: 0777777777.
-- ============================================================
USE ewallet;

INSERT INTO banks(name, cooperated_at, is_valid) VALUES
 ('Vietcombank', '2024-01-15', TRUE),
 ('BIDV', '2024-03-01', TRUE),
 ('Techcombank', '2024-06-20', TRUE),
 ('ACB', '2025-02-10', TRUE),
 ('MB Bank', '2025-09-05', TRUE);

INSERT INTO users(user_name, password_hash, email, phone) VALUES
 ('System Admin', SHA2('123456',256), 'admin@ewallet.vn', '0777777777'),
 ('Nguyen Van An', SHA2('123456',256), 'an@example.com', '0901000001'),
 ('Tran Thi Binh', SHA2('123456',256), 'binh@example.com', '0901000002'),
 ('Le Van Cuong', SHA2('123456',256), 'cuong@example.com', '0901000003');

INSERT INTO wallets(user_id, currency) VALUES
 (2,'VND'), (2,'USD'), (3,'VND'), (4,'VND'), (4,'USD');

INSERT INTO user_profiles(user_id, date_of_birth, age, sex, address, job, country) VALUES
 (2, '1998-04-12', 1, 'MALE', '12 Nguyen Hue, Ho Chi Minh City', 'Software engineer', 'Vietnam'),
 (3, '1992-09-21', 1, 'FEMALE', '5 Tran Phu, Da Nang', 'Accountant', 'Vietnam');
-- age is overwritten by the DOB trigger using today's date.

INSERT INTO bank_accounts(wallet_id, bank_id, account_number, status) VALUES
 (1,1,'012345678901','SUCCESS'),
 (1,2,'012345678902','SUCCESS'),
 (2,4,'012345678905','SUCCESS'),
 (3,1,'012345678903','SUCCESS'),
 (4,3,'012345678904','SUCCESS');

-- Each transaction is created as PENDING and settled to SUCCESS.
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL,1,'DEPOSIT',5000000.00);
SET @tx1 = LAST_INSERT_ID();
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=@tx1;

INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL,2,'DEPOSIT',300.00);
SET @tx2 = LAST_INSERT_ID();
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=@tx2;

INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL,3,'DEPOSIT',2000000.00);
SET @tx3 = LAST_INSERT_ID();
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=@tx3;

INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (1,3,'TRANSFER',1000000.00);
SET @tx4 = LAST_INSERT_ID();
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=@tx4;

INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (3,NULL,'WITHDRAW',500000.00);
SET @tx5 = LAST_INSERT_ID();
UPDATE transactions SET status='SUCCESS' WHERE transaction_id=@tx5;

INSERT INTO audit_logs(user_id, wallet_id, transaction_id, action) VALUES
 (2,NULL,NULL,'REGISTER'),
 (2,1,NULL,'CREATE_WALLET'),
 (2,1,NULL,'LINK_BANK'),
 (2,1,@tx4,'TRANSFER'),
 (3,3,@tx4,'TRANSFER_RECEIVED'),
 (3,3,@tx5,'WITHDRAW');

SELECT wallet_id,user_id,currency,balance,limit_week,remain_limit_week,status FROM wallets ORDER BY wallet_id;
