# Database - E-Wallet (MySQL 8.0+)

## Clean installation (practice project)

The database is rebuilt from scratch. **This permanently deletes the existing `ewallet` schema** when `--reset` is used. Back up anything you need first.

From the project root (Git Bash / WSL / Linux):

```bash
./database/install.sh root --reset --seed
```

- `root`: MySQL administrator account (change if yours differs).
- `--reset`: explicitly drops the old `ewallet` schema and creates it again.
- `--seed`: inserts demonstration users, wallets, partner banks, links, transactions and audit logs.

For a clean empty database, omit `--seed`:

```bash
./database/install.sh root --reset
```

The installer runs these files in order:

1. `migrations/All_Migrations.sql` - all seven core tables and indexes.
2. `trigger/All_Triggers.sql` - validation, immutable history, balance settlement and weekly limit reset.
3. `procedures/All_Procedures.sql` - every stored procedure used by the FastAPI repositories, including admin user/profile lists.
4. `migrations/009_create_user_for_clients.sql` - creates `ewallet_app` with `EXECUTE` only; no direct table access or `DELETE` privilege.
5. Optional `seed/sample_data.sql`.

## MySQL Workbench alternative

Run the same files manually, in the exact order above. Run `DROP DATABASE ewallet;` only if you intentionally want to erase the old practice database, then execute `All_Migrations.sql` first. Do not run the individual numbered migration files; `All_Migrations.sql` is the complete clean schema definition.

## Important business rules

- A profile stores `date_of_birth` before `age`. A trigger derives age from DOB; the API still uses the same `sp_user_profile_save` parameter contract.
- Partner banks are never deleted. `banks.is_valid=TRUE` means cooperating; `FALSE` means cooperation stopped.
- `bank_accounts.account_number` is stored before `status`. A link can only be cancelled; the historical row remains.
- Deposit requires an active partner-bank link on the receiving wallet.
- Withdrawal requires an active partner-bank link on the sending wallet.
- Transfer requires active links on both sender and receiver wallets, active wallets, same currency, sufficient balance and sufficient weekly transfer limit.
- Balances are updated only when a transaction moves from `PENDING` to `SUCCESS`.
- Users, profiles, wallets, banks, bank links, transactions and audit logs cannot be physically deleted by normal application operations. The API database account can execute approved stored procedures only.

## API compatibility

Stored procedure names and parameter order used by the existing Python repositories are preserved. Start the API from the project root:

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Ensure `config.json` contains database user `ewallet_app` and password `514160` (or change both the grant script and config together).
