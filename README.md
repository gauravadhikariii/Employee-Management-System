# Employee Management System — Q08: Improve User Satisfaction

Flask employee management app with SQLite for local development and PostgreSQL for hosted deployment.

## Run locally
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

## Demo login
- Username: `admin`
- Password: `Admin@123`

Change this password after first login. Do not use demo credentials for a public deployment.

## Deploy on Render + Neon
- Web app: Render Web Service
- Database: Neon PostgreSQL
- Set `DATABASE_URL` to the PostgreSQL connection string in Render Environment.
- Set `SECRET_KEY` to a long random secret in Render Environment.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

When `DATABASE_URL` is set, the app uses PostgreSQL; otherwise it uses local SQLite.

## Data migration
Existing records in local `database.db` do not automatically copy to Neon. Tables are created on first startup with `DATABASE_URL` configured. Add records again through the website or perform a separate migration.

## Security
Change the demo admin password immediately. Never commit `.env`, credentials, or database URLs to GitHub. Before real business use, add CSRF protection, account lockout/rate limiting, proper authorization, backups, and automated tests.
