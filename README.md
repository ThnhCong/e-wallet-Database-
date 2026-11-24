# e-wallet-Database-

## Safe profile and bank-link update

This update retains the existing REST contract (`POST /api/{operation}`) and the GUI background-worker / HTTP keep-alive design. `save_user_profile` now accepts `date_of_birth`; age is calculated by the service and database. `link_bank` now accepts `account_number`. New operations are `unlink_bank` and `admin_set_partner_bank_valid`.

For an existing database, back it up and run the updated `database/install.sh <mysql-admin-user>`. The installer is non-destructive by default and refreshes the schema, triggers and procedures without dropping records. `--reset` is explicitly destructive and requires typing `RESET`; never use it when preserving data matters. `--seed` only seeds a fresh schema.

Partner banks are retained and switched on/off using `banks.is_valid`. Bank links are retained and cancelled with `bank_accounts.status='CANCELLED'`. The application database account has no DELETE grant; database triggers also reject deletion of partner banks and bank-link history. Every wallet participating in deposit, withdrawal or transfer must have a successful link to a currently cooperating partner bank.

For rows that existed before this upgrade, the migration cannot know a customer's real
birth date from the old `age` field. It creates an estimated date of birth by subtracting
the stored age from the migration date; customers should correct this value in Personal
Details. Existing bank links receive a `LEGACY...` account-number placeholder because the
old schema did not store bank account numbers. To replace one, cancel the old link and
create a new link with the actual account number. Both old records remain available.
