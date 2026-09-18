USE ewallet;

INSERT INTO Transactions
(
    Transaction_id,
    Sender_id,
    Receiver_id,
    Type,
    Amount,
    Create_at,
    Status
)
VALUES
(
    1,
    NULL,
    1,
    'DEPOSIT',
    5000000.00,
    '2026-09-01 08:00:00',
    'SUCCESS'
),

(
    2,
    NULL,
    2,
    'DEPOSIT',
    3000000.00,
    '2026-09-01 08:30:00',
    'SUCCESS'
),

(
    3,
    NULL,
    3,
    'DEPOSIT',
    4000000.00,
    '2026-09-01 09:00:00',
    'SUCCESS'
),

(
    4,
    NULL,
    4,
    'DEPOSIT',
    3000000.00,
    '2026-09-01 09:15:00',
    'SUCCESS'
),

(
    5,
    NULL,
    5,
    'DEPOSIT',
    1000000.00,
    '2026-09-01 10:00:00',
    'SUCCESS'
),

(
    6,
    NULL,
    6,
    'DEPOSIT',
    2000000.00,
    '2026-09-02 08:00:00',
    'SUCCESS'
),

(
    7,
    NULL,
    7,
    'DEPOSIT',
    1000000.00,
    '2026-09-02 09:00:00',
    'SUCCESS'
),

(
    8,
    NULL,
    8,
    'DEPOSIT',
    3000000.00,
    '2026-09-02 10:00:00',
    'SUCCESS'
),

(
    9,
    1,
    NULL,
    'WITHDRAW',
    1000000.00,
    '2026-09-02 11:00:00',
    'SUCCESS'
),

(
    10,
    2,
    NULL,
    'WITHDRAW',
    500000.00,
    '2026-09-02 14:00:00',
    'SUCCESS'
),

(
    11,
    1,
    2,
    'TRANSFER',
    1000000.00,
    '2026-09-03 09:00:00',
    'SUCCESS'
),

(
    12,
    1,
    3,
    'TRANSFER',
    1000000.00,
    '2026-09-03 10:00:00',
    'SUCCESS'
),

(
    13,
    2,
    4,
    'TRANSFER',
    200000.00,
    '2026-09-03 11:30:00',
    'SUCCESS'
),

(
    14,
    4,
    1,
    'TRANSFER',
    1000000.00,
    '2026-09-04 08:30:00',
    'SUCCESS'
),

(
    15,
    4,
    5,
    'TRANSFER',
    500000.00,
    '2026-09-04 09:00:00',
    'SUCCESS'
),

(
    16,
    5,
    6,
    'TRANSFER',
    100000.00,
    '2026-09-04 10:00:00',
    'SUCCESS'
),

(
    17,
    NULL,
    10,
    'DEPOSIT',
    1500000.00,
    '2026-09-05 13:00:00',
    'SUCCESS'
),

(
    18,
    1,
    4,
    'TRANSFER',
    5000000.00,
    '2026-09-05 14:00:00',
    'FAIL'
),

(
    19,
    4,
    10,
    'TRANSFER',
    100000000.00,
    '2026-09-05 15:00:00',
    'FAIL'
),

(
    20,
    1,
    10,
    'TRANSFER',
    500000.00,
    '2026-09-06 16:00:00',
    'SUCCESS'
);
