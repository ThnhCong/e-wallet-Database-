#!/usr/bin/env bash
# Re-create the whole e-wallet database from scratch (DROP + CREATE). For practice / demo only.
# Usage: ./database/install.sh <mysql-admin-user> [--seed]
set -euo pipefail
ADMIN="${1:-root}"; SEED="${2:-}"
cd "$(dirname "$0")"
read -r -s -p "Password of MySQL user '$ADMIN': " PW; echo
run() { mysql -u"$ADMIN" -p"$PW" "$@"; }
run -e "DROP DATABASE IF EXISTS ewallet;"
run < migrations/All_Migrations.sql            # 7 tables + indexes
run < trigger/All_Triggers.sql                 # 10 triggers + weekly-reset event
run < procedures/All_Procedures.sql            # stored procedures
run < migrations/009_create_user_for_clients.sql   # application DB account (edit the password first)
[ "$SEED" = "--seed" ] && run < seed/sample_data.sql
echo "Done. Next: edit ../config.json, then  python -m src.api   and   python -m GUI.main"
