# EWallet Desktop Client

This folder contains the desktop client only. The GUI communicates with the FastAPI server over HTTP; it does not connect directly to MySQL.

## Configure the API address

Edit `client_config.json` and set `api.base_url` to the public Cloudflare Tunnel URL (or the LAN/VPN API address). The client reads this file from the same directory as the executable. `EWALLET_API_URL`, when set, takes precedence over the JSON file. If neither is configured, the client falls back to `http://127.0.0.1:8000`.

For a Cloudflare Quick Tunnel, update this value whenever Cloudflare assigns a new URL. A Named Tunnel provides a stable hostname.

## Build

Install `requirements.txt`, then build from this directory. Keep `client_config.json` beside the generated executable so the API address can be changed without rebuilding.

Example:

```powershell
python -m PyInstaller --noconfirm --clean --onedir --windowed --name EWallet --add-data "GUI/theme;GUI/theme" --add-data "client_config.json;." --collect-submodules httpx --collect-submodules httpcore --collect-submodules h2 GUI/main.py
```

The API server and MySQL database must be started separately on the server machine.
