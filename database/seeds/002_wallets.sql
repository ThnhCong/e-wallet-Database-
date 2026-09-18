INSERT INTO wallets (
    user_id,
    balance,
    currency,
    limit_week
)
SELECT
    user_id,
    0.00,
    'VND',
    10000000.00
FROM users
WHERE email IN (
    'alice@example.com',
    'bob@example.com',
    'charlie@example.com'
);
