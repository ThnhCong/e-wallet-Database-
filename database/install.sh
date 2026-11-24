#!/usr/bin/env bash
# Fresh installer for the ewallet schema. Existing data is never dropped unless --reset is explicit.
# Usage: ./database/install.sh [mysql-admin-user] [--reset] [--seed]
set -euo pipefail
ADMIN="${1:-root}"
RESET="false"
SEED="false"
for arg in "${@:2}"; do
  case "$arg" in
    --reset) RESET="true" ;;
    --seed) SEED="true" ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done
cd "$(dirname "$0")"
read -r -s -p "Password of MySQL administrator '$ADMIN': " PW
echo
run_mysql() { mysql --default-character-set=utf8mb4 -u"$ADMIN" -p"$PW" "$@"; }

EXISTS="$(run_mysql -N -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='ewallet'")"
if [[ "$EXISTS" == "1" ]]; then
  if [[ "$RESET" != "true" ]]; then
    echo "Database 'ewallet' already exists. No changes were made."
    echo "For a clean practice installation, rerun with: ./database/install.sh $ADMIN --reset --seed"
    exit 1
  fi
  echo "WARNING: this will permanently drop the entire ewallet database."
  read -r -p "Type RESET to confirm: " CONFIRM
  [[ "$CONFIRM" == "RESET" ]] || { echo "Cancelled."; exit 1; }
  run_mysql -e "DROP DATABASE ewallet;"
fi

run_mysql < migrations/All_Migrations.sql
run_mysql < trigger/All_Triggers.sql
run_mysql < procedures/All_Procedures.sql
run_mysql < migrations/009_create_user_for_clients.sql
if [[ "$SEED" == "true" ]]; then
  run_mysql < seed/sample_data.sql
fi

echo "Fresh ewallet database created successfully."
echo "API DB account: ewallet_app (password must match config.json)."
echo "Start API from project root: python -m uvicorn src.api:app --host 0.0.0.0 --port 8000"
