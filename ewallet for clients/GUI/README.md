# E-Wallet GUI

The PySide6 interface is the Presentation Layer. It communicates with the FastAPI REST service through `core/api.py`; GUI widgets and pages contain no SQL or direct service calls.

## Run

From the project root, install dependencies, configure `config.json`, start the REST API with `python -m src.api`, then start the GUI:

```bash
python -m GUI.main
```

The MySQL schema, stored procedures and triggers must be installed. The API reads database settings and admin phone numbers from the server-side project-root `config.json`. The GUI uses `EWALLET_API_URL` (default `http://127.0.0.1:8000`) and does not need database credentials.

## Structure

- `main.py`, `main_window.py`: application entry point and authenticated shell.
- `app_state.py`: current signed-in user and server-provided admin flag.
- `core/api.py`: authenticated HTTP client for the REST API.
- `core/router.py`: named page navigation.
- `core/worker.py`: reusable QRunnable helper for future background operations.
- `pages/`: authentication, dashboard, wallets, financial operations, history, profile, settings, and administration.
- `widgets/`: shared tables, amount input, sidebar, confirmation and notification dialogs.
- `theme/`: QSS stylesheets and theme loader.

Financial requests are handled by the REST API and existing Application Layer. The GUI does not update wallet balances directly; database triggers remain responsible for balance and weekly-limit changes.

## QSS themes

QSS is Qt's stylesheet language, similar to CSS. `light.qss` and `dark.qss` define the colors, borders, spacing and states of shared widgets. `theme_manager.py` loads one stylesheet for the whole application. To start with the dark theme, change `apply_theme(app, "light")` in `main.py` to `apply_theme(app, "dark")`.
