USE ewallet;

INSERT INTO AuditLogs
    (User_id, Wallet_id, Transaction_id, Action, Entry_type, Time)
VALUES

-- User registration
(1, NULL, NULL, 'REGISTER_ACCOUNT', NULL,
 '2026-09-01 07:30:00'),

-- Deposit: User receives money -> CREDIT
(1, 1, 1, 'DEPOSIT', 'CREDIT',
 '2026-09-01 08:00:00'),

(2, 2, 2, 'DEPOSIT', 'CREDIT',
 '2026-09-01 08:30:00'),

(3, 3, 3, 'DEPOSIT', 'CREDIT',
 '2026-09-01 09:00:00'),

(4, 4, 4, 'DEPOSIT', 'CREDIT',
 '2026-09-01 09:15:00'),

(5, 5, 5, 'DEPOSIT', 'CREDIT',
 '2026-09-01 10:00:00'),

(6, 6, 6, 'DEPOSIT', 'CREDIT',
 '2026-09-02 08:00:00'),

(7, 7, 7, 'DEPOSIT', 'CREDIT',
 '2026-09-02 09:00:00'),

(8, 8, 8, 'DEPOSIT', 'CREDIT',
 '2026-09-02 10:00:00'),


-- Withdraw: User sends money out -> DEBIT
(1, 1, 9, 'WITHDRAW', 'DEBIT',
 '2026-09-02 11:00:00'),

(2, 2, 10, 'WITHDRAW', 'DEBIT',
 '2026-09-02 14:00:00'),


-- Transfer transaction 11
-- Sender -> DEBIT
(1, 1, 11, 'TRANSFER', 'DEBIT',
 '2026-09-03 09:00:00'),

-- Receiver -> CREDIT
(2, 2, 11, 'TRANSFER', 'CREDIT',
 '2026-09-03 09:00:00'),


-- Transfer transaction 12
(1, 1, 12, 'TRANSFER', 'DEBIT',
 '2026-09-03 10:00:00'),

(3, 3, 12, 'TRANSFER', 'CREDIT',
 '2026-09-03 10:00:00'),


-- Transfer transaction 13
(2, 2, 13, 'TRANSFER', 'DEBIT',
 '2026-09-03 11:30:00'),

(4, 4, 13, 'TRANSFER', 'CREDIT',
 '2026-09-03 11:30:00'),


-- Transfer transaction 14
(4, 4, 14, 'TRANSFER', 'DEBIT',
 '2026-09-04 08:30:00'),

(1, 1, 14, 'TRANSFER', 'CREDIT',
 '2026-09-04 08:30:00'),


-- Transfer transaction 15
(4, 4, 15, 'TRANSFER', 'DEBIT',
 '2026-09-04 09:00:00'),

(5, 5, 15, 'TRANSFER', 'CREDIT',
 '2026-09-04 09:00:00'),


-- Transfer transaction 16
(5, 5, 16, 'TRANSFER', 'DEBIT',
 '2026-09-04 10:00:00'),

(6, 6, 16, 'TRANSFER', 'CREDIT',
 '2026-09-04 10:00:00'),


-- Deposit to User 10
(10, 10, 17, 'DEPOSIT', 'CREDIT',
 '2026-09-05 13:00:00'),


-- Failed transfer
-- No financial ledger entry because transaction failed.
(1, 1, 18, 'TRANSFER_FAILED', NULL,
 '2026-09-05 14:00:00'),


-- Failed transfer because amount is too large
(4, 4, 19, 'TRANSFER_FAILED', NULL,
 '2026-09-05 15:00:00'),


-- Successful transfer transaction 20
(1, 1, 20, 'TRANSFER', 'DEBIT',
 '2026-09-06 16:00:00'),

(10, 10, 20, 'TRANSFER', 'CREDIT',
 '2026-09-06 16:00:00');
