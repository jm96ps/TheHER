# Deploy on Render - TODO

1. Ensure project is a Django app with `manage.py` at repo root.
2. Confirm `requirements.txt` includes `gunicorn` (for WSGI) or `daphne`/`uvicorn` for ASGI.
3. Add a minimal `render.yaml` (optional) or create a Web Service in Render dashboard.
   - Build command: `pip install -r requirements.txt`
   - Start command (WSGI): `gunicorn webapp.wsgi:application --bind 0.0.0.0:$PORT`
4. Configure `settings.py` for production via environment variables:
   - `SECRET_KEY` from env
   - `DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'`
   - `ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')`
   - Support `DATABASE_URL` if using an external DB (use `dj-database-url`).
5. Ensure static files are collected during deploy:
   - Add `python manage.py collectstatic --noinput` to build or release commands.
6. Add health/readiness endpoint (Django view) and map it to `/health`.
7. Add environment variables in Render: `SECRET_KEY`, `DEBUG=false`, DB credentials if needed.
8. (Optional) Use a `Procfile` or `render.yaml` to codify commands and environment.
9. Post-deploy checks:
   - Visit the root URL and `/health`.
   - Verify static files load and uploads/exports work.
   - Check logs in Render for errors.

Notes:
- If you prefer containers, build a small Dockerfile and use Render's Docker deploy option.
- For background tasks, add a separate Worker service on Render.
