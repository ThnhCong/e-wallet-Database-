# Stored Procedures

Install order (or simply run `database/install.sh <admin-user> --seed`):

1. `database/migrations/All_Migrations.sql`  (7 tables + indexes)
2. `database/trigger/All_Triggers.sql`        (10 triggers + weekly reset event)
3. `database/procedures/All_Procedures.sql`   (all procedures below, run once)
4. `database/migrations/009_create_user_for_clients.sql` as a MySQL administrator, after changing the sample password
5. optional: `database/seed/sample_data.sql` (valid sample data) and `database/seed/demo_violations.sql` (statements that must fail)
6. Configure `config.json` (database + admin phone numbers). The GUI only needs `EWALLET_API_URL`.

| File | Procedures |
|---|---|
| user_procedures.sql | sp_user_create, sp_user_get_by_phone, sp_user_get_with_hash, sp_user_get_by_id, sp_user_update_profile, sp_user_update_password |
| wallet_procedures.sql | sp_wallet_create, sp_wallet_get_by_id, sp_wallet_list_by_user, sp_wallet_list_all, sp_wallet_lock_many, sp_wallet_set_status |
| transaction_procedures.sql | sp_transaction_create, sp_transaction_set_status, sp_transaction_get, sp_transaction_list_user, sp_transaction_list_all |
| audit_procedures.sql | sp_audit_create, sp_audit_list |
| user_profile_procedures.sql | sp_user_profile_get, sp_user_profile_save (upsert), sp_admin_list_user_profiles (filtered + paginated admin list) |
| bank_procedures.sql | sp_bank_list, sp_bank_get, sp_bank_account_link, sp_bank_account_list_by_user, sp_bank_account_list_all |
| statistics_procedures.sql | sp_user_statistics, sp_bank_statistics, sp_admin_system_statistics |
| admin_procedures.sql | sp_admin_list_users |

## Transaction boundary
The procedures intentionally do not issue `START TRANSACTION`, `COMMIT` or `ROLLBACK`. The Python services group several procedure calls in one `db_transaction` (commit on success, rollback on any error), so registration, financial operations and audit logging stay atomic. The triggers validate transactions and move the money.

## Update Customer Profiles listing on an existing database

If the database already exists, run `update_user_profile_procedure.sql` in MySQL Workbench (or execute it with the MySQL client) to replace `sp_admin_list_user_profiles`. This does not drop tables or delete data. Then stop the old API process with Ctrl+C and restart it from the project root:

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

For a complete fresh installation, run `database/migrations/All_Migrations.sql`, `database/trigger/All_Triggers.sql`, `database/procedures/All_Procedures.sql`, and the application-user grant script in that order. The Customer Profiles endpoint now receives an explicit zero count even when `user_profiles` is empty; the GUI displays an empty state instead of treating that condition as an error.
> MySQL 8.0 collation standard: this project uses `utf8mb4_0900_ai_ci` for the database, text columns, and stored-procedure string parameters. Run `update_user_profile_procedure.sql` to normalize an existing database before testing Customer Profiles.
