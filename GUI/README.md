# E-Wallet GUI

The PySide6 interface is the Presentation Layer. It calls the existing controllers through `core/api.py`; GUI widgets and pages contain no SQL.

## Run

From the project root, install the project's dependencies and start the GUI:

```bash
python -m GUI.main
```

The MySQL database, migrations, triggers, event scheduler, and connection settings in `src/config/database/connection.py` must already be configured.

## Structure

- `main.py`, `main_window.py`: application entry point and authenticated shell.
- `app_state.py`: current signed-in user and role.
- `core/api.py`: short-lived database connection and controller bridge.
- `core/router.py`: named page navigation.
- `core/worker.py`: reusable QRunnable helper for future background operations.
- `pages/`: authentication, dashboard, wallets, financial operations, history, profile, settings, and administration.
- `widgets/`: shared tables, amount input, sidebar, confirmation and notification dialogs.
- `theme/`: QSS stylesheets and theme loader.

Financial requests use the existing Application Layer. The GUI does not update wallet balances directly; database triggers remain responsible for balance and weekly-limit changes.

## QSS themes

QSS is Qt's stylesheet language, similar to CSS. `light.qss` and `dark.qss` define the colors, borders, spacing and states of shared widgets. `theme_manager.py` loads one stylesheet for the whole application. To start with the dark theme, change `apply_theme(app, "light")` in `main.py` to `apply_theme(app, "dark")`.
