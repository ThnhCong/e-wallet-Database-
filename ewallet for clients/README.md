# ewallet for clients
This is a part for clients.
Client just has GUI and it calls FAST API at a virtual address which is created by cloudflare 
(https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/?utm_source=chatgpt.com).
Before creating virtual address by cloudflare you need to run e-wallet-Databse-/src/api.py.
After installing cloudflare and creating a domain for the FAST API you have to edit API HOST in client_config.spec into the current address.