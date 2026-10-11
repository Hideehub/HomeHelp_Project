# Deploying HomeHelp

The app is a Flask app served by gunicorn (`wsgi:app`), backed by MySQL, with user photos saved to disk. This guide uses [Railway](https://railway.com) because it provides MySQL, a persistent volume for uploads, and HTTPS in one place. Any host that runs a Procfile works the same way.

## 0. Before anything else: rotate leaked secrets

Earlier commits on GitHub contain a Paystack secret key, the Flask `SECRET_KEY`, a mail password and a database URI. Removing them from the code does not remove them from git history, so treat all of them as public:

1. **Paystack** → Settings → API Keys & Webhooks → generate new secret keys (test and live).
2. **Gmail** → Google Account → Security → App passwords → revoke the old one, create a new one.
3. **Database** → change the password of the MySQL user that was in the old URI.
4. **SECRET_KEY** → generate a new one: `python -c "import secrets; print(secrets.token_hex(32))"`.

Put the new values only in `.env` (local) and in Railway's Variables (production).

## 1. Project layout for deployment

| File | Purpose |
|---|---|
| `wsgi.py` | Entry point for gunicorn |
| `Procfile` | `web:` start command, `release:` runs migrations (on hosts that support it) |
| `requirements.txt` | Pinned dependencies |
| `.python-version` | Python version for the build (3.12) |
| `.env.example` | Every setting the app reads, with explanations |
| `homehelp/config.py` | Reads all settings from environment variables |
| `homehelp/commands.py` | `flask seed-states`, `flask add-category`, `flask create-admin` |

The app refuses to start if `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI` or `PAYSTACK_SECRET_KEY` is missing.

## 2. Run it locally first

```bash
python3 -m venv vhomehelp && source vhomehelp/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in real values
flask --app wsgi db upgrade
flask --app wsgi seed-states
flask --app wsgi add-category Cleaner Cook Nanny Driver Painter
flask --app wsgi create-admin
python starter.py             # http://127.0.0.1:5000 (FLASK_DEBUG=1 for debug mode)
```

Test a full payment with a Paystack **test** key and test card `4084 0840 8408 4081`, CVV `408`, any future expiry, PIN `0000`, OTP `123456`.

## 3. Deploy on Railway

1. **Create the project.** railway.com → New Project → Deploy from GitHub repo → `HomeHelp_Project`.
2. **Add MySQL.** In the project: New → Database → MySQL.
3. **Set variables** on the web service (Variables tab):

   ```
   SECRET_KEY=<new random value>
   SQLALCHEMY_DATABASE_URI=mysql+pymysql://${{MySQL.MYSQLUSER}}:${{MySQL.MYSQLPASSWORD}}@${{MySQL.MYSQLHOST}}:${{MySQL.MYSQLPORT}}/${{MySQL.MYSQLDATABASE}}
   PAYSTACK_SECRET_KEY=sk_test_...        # switch to sk_live_ only after testing
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=465
   MAIL_USE_SSL=True
   MAIL_USE_TLS=False
   MAIL_USERNAME=...
   MAIL_PASSWORD=<new app password>
   MAIL_DEFAULT_SENDER=...
   PROXY_COUNT=1
   SESSION_COOKIE_SECURE=True
   ```

   `PROXY_COUNT=1` makes the Paystack callback URL use your real `https://` domain. `SESSION_COOKIE_SECURE=True` keeps the login cookie on HTTPS only.

4. **Add a volume for uploads.** Right-click the web service → Attach Volume → mount path:
   `/app/homehelp/static/images/uploads`
   Without this, every redeploy deletes users' photos.
5. **Run migrations on every deploy.** Service → Settings → Deploy → Pre-deploy command:
   `flask --app wsgi db upgrade`
6. **Get a domain.** Settings → Networking → Generate Domain (or add your own).
7. **Seed data once.** Install the Railway CLI, then from the project folder:

   ```bash
   railway link
   railway run flask --app wsgi seed-states
   railway run flask --app wsgi add-category Cleaner Cook Nanny Driver Painter
   railway run flask --app wsgi create-admin
   ```

   (`railway run` uses the production variables. If it can't reach the database host from your machine, use the MySQL service's public URL for that command, or run the commands from the service's shell.)

## 4. Going live checklist

- [ ] All four secrets rotated (step 0)
- [ ] Full flow tested on the deployed site with a Paystack **test** key: employer pays → sends job → helper accepts → employer marks complete → helper's wallet is credited → helper requests withdrawal → admin marks it processed
- [ ] Cancel and reject both refund the employer's wallet exactly once
- [ ] Upload a profile photo, redeploy, and check that the photo is still there (volume works)
- [ ] Job email arrives (if Gmail SMTP is blocked by the host, use an SMTP provider such as Brevo or Mailgun on port 587 with `MAIL_USE_TLS=True`, `MAIL_USE_SSL=False`)
- [ ] Switch `PAYSTACK_SECRET_KEY` to `sk_live_...`
- [ ] Database backups enabled (Railway MySQL → Backups)

## 5. How money moves (for whoever runs the admin side)

- An employer's payment is only marked **paid** after Paystack confirms `success` for the exact amount.
- Each paid payment funds exactly **one** job (`jobposting.post_payid`).
- Helper rejects, or employer cancels before completion → payment **refunded** to the employer's wallet.
- Employer marks an accepted job complete → payment **credited** to the helper's wallet.
- Withdrawals deduct the wallet immediately and appear in Admin → Withdrawals. The admin pays the bank account by hand, then clicks to mark it processed.

Jobs created before this change have no linked payment, so cancelling or completing them moves no money. Settle any of those by hand.

## Later improvements (not blocking launch)

- A Paystack **webhook** (`charge.success`) so payments are confirmed even if the employer closes the browser before returning to the site.
- Paying out withdrawals automatically through Paystack Transfers instead of by hand.
- Rate limiting on login pages (e.g. Flask-Limiter).
- Automated tests in the repo.
