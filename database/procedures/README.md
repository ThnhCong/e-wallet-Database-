# Stored Procedures

Install in this order:

1. Run `database/migrations/All_Migrations.sql`.
2. Run `database/trigger/All_Triggers.sql`.
3. Run `database/procedures/All_Procedures.sql` once. This file contains all procedures below.
4. Run the updated `database/migrations/006_create_user_for_clients.sql` as a MySQL administrator, after changing the sample credentials.
5. Configure database connection values and admin phone numbers in the server-side project-root `config.json` (or override DB settings with environment variables). The GUI connects through `EWALLET_API_URL` and never receives database credentials.

Individual procedure files can also be run separately:

- `user_procedures.sql`
- `wallet_procedures.sql`
- `transaction_procedures.sql`
- `audit_procedures.sql`
- `admin_procedures.sql`

## Transaction boundary

The procedures intentionally do not issue `START TRANSACTION`, `COMMIT`, or `ROLLBACK`. Existing Python Services coordinate multiple procedure calls with `db_transaction`, preserving atomic registration, financial operations, and audit logging. The transaction triggers continue to validate transactions and update balances. This also preserves the existing behavior where a transaction that cannot be settled is recorded as `FAIL` before the service returns the translated error.
