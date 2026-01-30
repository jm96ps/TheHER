# Deployment to Render — TheHER

This file documents the minimal steps to deploy `TheHER` Django app to Render.

Prerequisites
- Git remote (e.g., GitHub) with your repository pushed.
- A Render account.

Quick checklist
1. Push all changes to your remote branch (e.g., `main`).
   - `git add . && git commit -m "Prepare render deploy" && git push origin main`
2. In Render, create a new **Web Service** and connect your repo (or use `render.yaml`).
   - Branch: `main` (or whichever branch you prefer)
   - Build command: `pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start command: `gunicorn theher_django.wsgi --log-file -`

Required environment variables (set in Render dashboard)
- `DJANGO_SECRET_KEY` — secure random string (do NOT commit).
- `DJANGO_DEBUG` — `False` for production.
- `DJANGO_ALLOWED_HOSTS` — e.g., `yourdomain.com` or `*` during testing.
- `DATABASE_URL` — provided by Render Managed Postgres if used (optional; sqlite fallback exists but not recommended).

Notes on static files
- WhiteNoise is configured in `theher_django/settings.py`.
- Render build runs `collectstatic` (see buildCommand). Static files are collected to `STATIC_ROOT` and served by WhiteNoise.

Database and migrations
- If using Render Managed Postgres: add the Postgres add-on and set `DATABASE_URL` in env.
- After first deploy, run migrations from Render Shell or via dashboard:
  - `python manage.py migrate`
  - (Optional) create superuser: `python manage.py createsuperuser`

Local testing (optional)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Common troubleshooting
- `ModuleNotFoundError: Django` — ensure `pip install -r requirements.txt` succeeded and the correct Python version is used.
- `collectstatic` fails — verify `STATIC_ROOT` exists or is writable and check for missing static files imports.
- Database connection errors — confirm `DATABASE_URL` is properly set and reachable.

Optional improvements
- Use Render Managed Postgres for production data.
- Configure HTTPS/custom domains in Render settings.
- Add CI to run tests and linters before deploy.

If you want, I can:
- Create a Render service using `render.yaml` (I cannot call Render API from here without credentials).
- Add a GitHub Actions workflow to run tests and deploy automatically.
