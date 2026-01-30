# TheHER — HER fitting web application

Minimal README: how to run and where to find features.

Requirements
- Python 3.10+ (recommended)
- Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run (development)

```powershell
python -m webapp.app
# or run the Django server:
# python manage.py runserver
```

Open `http://127.0.0.1:8000/` (or the address shown) and use the dashboard:
- Run Fit: upload LSV-like data, select columns and separator
- Experimental Parameters: set `E_ref`, `pH`, electrode area `A_e`, and ohmic drop ΔR
- Fitting Parameters: choose `simplified` or `full`, set `β_v`, `β_h`, and fitting method

Documentation page
- A concise Documentation page is available in the site menu (Docs)

Development notes
- Core model: `webapp/models/hydrogen.py`
- Service layer: `webapp/services/fitting_service.py`
- Django views: `her/views.py` (reuse service functions)
- Templates: `webapp/templates/` and `her/templates/` (dashboard)

Testing
- Run unit tests with `pytest` if installed:

```powershell
pytest -q
```

License
- MIT (see `LICENSE`)

Contact
- For issues or questions open an issue or email: jamesmario@usp.br

---

**Last Updated**: January 2026
**Status**: Active Development ✓
