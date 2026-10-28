# NSLA Tyre Package Platform

Blue-and-white, mobile-first Flask + SQLite web app with registration/login, referral codes, package catalog, package purchases, locked packages, account balance ledger, deposit/withdrawal requests, and admin review.

## Run on Android (Termux)
1. Put this folder at `~/NSLA`.
2. Run:
   ```sh
   pkg install python unzip -y
   cd ~/NSLA
   pip install -r requirements.txt
   export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
   export ADMIN_USERNAME="nslaadmin"
   export ADMIN_PASSWORD="choose-a-long-unique-password"
   python app.py
   ```
3. Open `http://127.0.0.1:5000` on the same phone.

## Admin
Sign in using the configured admin username/password, then open `/admin`. On Render, set `ADMIN_PASSWORD` as a secret environment variable before deployment.

## Payment processing
Deposit and withdrawal forms create pending requests. Admin must independently verify receipt in the actual MTN/Airtel account before approving a deposit. For a withdrawal, send the payout first, then approve the request. This project does **not** include MTN MoMo/Airtel Money API credentials or automatic transfers; those require an approved provider integration.

## Important financial note
The platform records package purchases and account transactions. It does not automatically manufacture profits or guarantee the displayed package figures as investment returns. Only credit funds that the business can actually pay. Obtain appropriate legal/compliance advice before offering investments or financial products.

## Database
SQLite data is stored in `nsla.db` locally, or at `DATABASE_PATH` when configured. Keep persistent storage enabled on hosting.
