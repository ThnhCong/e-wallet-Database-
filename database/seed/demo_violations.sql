-- =====================================================================
-- VIOLATION SCENARIOS: every statement below must FAIL.  Run each one separately (or use
-- `mysql --force`) after sample_data.sql.  The expected message is in the comment.
-- =====================================================================
USE ewallet;

-- 1. Transfer more than the balance                -> Insufficient balance
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (3, 1, 'TRANSFER', 99999999);
-- 2. Transfer above the weekly limit (10,000,000)  -> Weekly transfer limit exceeded
--    (first fund wallet 4 with a valid deposit so that the balance is NOT the problem)
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL, 4, 'DEPOSIT', 15000000);
UPDATE transactions SET status='SUCCESS' WHERE transaction_id = LAST_INSERT_ID();
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (4, 3, 'TRANSFER', 12000000);
-- 3. Transfer between different currencies         -> Sender and receiver must use the same currency
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (1, 2, 'TRANSFER', 1000);
-- 4. Transfer to the same wallet                   -> Sender and receiver cannot be the same wallet
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (1, 1, 'TRANSFER', 1000);
-- 5. Deposit with a sender                         -> DEPOSIT requires a receiver and no sender
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (1, 3, 'DEPOSIT', 1000);
-- 6. Negative amount                               -> chk_transactions_amount / Amount must be greater than 0
INSERT INTO transactions(sender_id, receiver_id, type, amount) VALUES (NULL, 1, 'DEPOSIT', -5);
-- 7. Edit the balance directly                     -> Balance can only be changed by a successful transaction
UPDATE wallets SET balance = 999999999 WHERE wallet_id = 1;
-- 8. Modify a finished transaction                 -> Completed transactions cannot be modified
UPDATE transactions SET amount = 1 WHERE transaction_id = 1;
-- 9. Delete a transaction                          -> Transactions cannot be deleted
DELETE FROM transactions WHERE transaction_id = 1;
-- 10. Delete a wallet with history                 -> Wallet with transaction history cannot be deleted
DELETE FROM wallets WHERE wallet_id = 1;
-- 11. Modify / delete an audit log                 -> Audit logs cannot be modified / deleted
UPDATE audit_logs SET action = 'LOGIN' WHERE audit_log_id = 1;
DELETE FROM audit_logs WHERE audit_log_id = 1;
-- 12. Unsupported currency                         -> Unsupported currency
INSERT INTO wallets(user_id, currency) VALUES (2, 'EUR');
-- 13. Second profile for the same user (1:1)       -> Duplicate entry ... uq_user_profiles_user_id
INSERT INTO user_profiles(user_id, age, sex, address, job, country) VALUES (2, 30, 'MALE', 'x', 'y', 'z');
-- 14. Invalid age                                  -> chk_user_profiles_age
INSERT INTO user_profiles(user_id, age, sex, address, job, country) VALUES (4, 200, 'MALE', 'x', 'y', 'z');
-- 15. Link the same wallet to the same bank twice  -> Wallet is already linked to this bank
INSERT INTO bank_accounts(wallet_id, bank_id) VALUES (1, 1);
-- 16. Link a LOCKED wallet                         -> Wallet is locked
UPDATE wallets SET status = 'LOCKED' WHERE wallet_id = 5;
INSERT INTO bank_accounts(wallet_id, bank_id) VALUES (5, 1);
UPDATE wallets SET status = 'ACTIVE' WHERE wallet_id = 5;
-- 17. Link to a bank that does not exist           -> Bank does not exist
INSERT INTO bank_accounts(wallet_id, bank_id) VALUES (4, 999);
-- 18. Delete a bank that has links                 -> foreign key (RESTRICT)
DELETE FROM banks WHERE bank_id = 1;
