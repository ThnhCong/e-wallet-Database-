# Aurelia E-Wallet GUI

The PySide6 desktop client communicates only with the FastAPI REST API through `GUI/core/api.py`. It does not connect directly to MySQL or instantiate backend services.

## User workspace

- Overview dashboard and recent transactions
- Wallet creation, balances, weekly limits, lock/unlock
- Simulated deposits and withdrawals
- Wallet-to-wallet transfers
- Transaction history and transaction detail lookup
- Basic account profile (name, email, phone)
- Additional personal details (age, sex, address, occupation, country)
- Partner-bank directory and simulated wallet-bank linking
- Per-currency activity statistics with optional date range
- Account activity/audit timeline
- Password change

## Administrator workspace

- System-wide statistics overview
- Customer directory and customer profile lookup
- Wallet monitoring and lock/unlock
- All transaction listing and filtering
- Audit log review
- Bank connection listing
- Partner-bank statistics

## Important behavior

Bank linking and deposits are simulated by the existing backend. The GUI does not connect to external banks or payment rails. Only actions exposed by the REST API are presented; read-only backend functions remain read-only in the desktop client.

## Run

Start the API server first, then launch `python -m GUI.main` from the project root. Set `EWALLET_API_URL` when the API is hosted somewhere other than `http://127.0.0.1:8000`.
