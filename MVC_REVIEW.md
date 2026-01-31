# MVC Review

- Views: `her/views.py` delegates to `webapp.services.fitting_service`.
- Services: `webapp/services/fitting_service.py` contains fitting orchestration and I/O.
- Models: `webapp/models/hydrogen.py` encapsulates fitting model and data.

Assessment:
- Separation is adequate: views handle HTTP, services do heavy work, models contain numeric code.
- Suggestion: move file parsing and validation into a small `webapp.utils.parsers` module to keep services focused on orchestration.
- Suggestion: add small unit-test files under `tests/` for `fitting_service` and `hydrogen` model.

Action items:
- Add `webapp/utils/parsers.py` to centralize file parsing and validation.
- Add `tests/test_fitting_service.py` with minimal fixtures and a smoke test using the sample CSV.
- Add CI job to run tests (GitHub Actions or Render's build checks).
