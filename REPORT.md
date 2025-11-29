Report — To-Do List improvements

Overview
--------
This repository received a set of focused improvements to the UI, UX, server-side account management, tests, and monitoring. The goal was to: fix the hamburger menu, make login/signup and account pages match an ocean glassmorphism theme, add account management (change username/password/delete), increase test coverage, and add a minimal Prometheus + Grafana monitoring stack.

What changed (high level)
-------------------------
- UI / Frontend
  - `templates/login.html`, `templates/signup.html` updated to use the glassmorphism theme and show placeholders inside inputs (autocomplete attributes added).
  - New `templates/landing.html` created (big "SIENE" title and CTAs).
  - `static/styles.css` extended with glass button styles, input styles, landing styles, and accessibility helpers.
  - Hamburger markup consolidated: inline script removed and `static/app.js` enhanced with a robust, idempotent `initHamburger()` to avoid duplicate listeners.

- Account management
  - `templates/account.html` added/updated to provide a themed account page with forms to change username, change password, and delete account.
  - `server.py` updated: `/account` route now implements POST handling for update_username, update_password, and delete_account (with confirmation). Logout behavior preserved.

- Tests and coverage
  - `tests/test_server_extra.py` added with tests for health/metrics endpoints, index redirect behavior, signup/login/logout flow, and account update/delete flows.
  - Existing tests were left in place; overall test suite was extended to exercise new server paths.

- Monitoring (Prometheus + Grafana)
  - `prometheus.yml` (already present) targets the app metrics endpoint.
  - New `docker-compose.yml` added to bring up Prometheus and Grafana quickly.
  - Grafana provisioning files and `grafana/dashboards/todo_dashboard.json` added — the dashboard is auto-imported by Grafana on startup.
  - `MONITORING.md` included with quick-start instructions and notes about host networking on macOS/Windows.

How to run & verify (quick)
---------------------------
1. Install Python deps and run the app (app runs by default on port 5001):

   ```bash
   python -m venv .venv          # optional
   source .venv/bin/activate
   pip install -r requirements.txt
   python server.py
   ```

2. Manual UI checks
   - Landing: http://127.0.0.1:5001/
   - Login: http://127.0.0.1:5001/login
   - Signup: http://127.0.0.1:5001/signup
   - Account: http://127.0.0.1:5001/account (requires login)

3. Tests
   - Run the test suite:
     ```bash
     pytest -q
     ```
   - If you want coverage, install pytest-cov and run:
     ```bash
     pip install pytest-cov
     pytest --cov=server
     ```

4. Monitoring stack (Prometheus + Grafana)
   - Start the stack (requires Docker):
     ```bash
     docker compose up -d
     ```
   - Prometheus UI: http://localhost:9090 (check Targets)
   - Grafana UI: http://localhost:3000 (admin/admin); "To-Do App Overview" dashboard is auto-provisioned

Notes & rationale
-----------------
- The hamburger fix centralizes behavior in `static/app.js` to make the listener idempotent and resilient to script load order.
- Account management happens server-side with cautious checks (password verification, username uniqueness, DELETE confirmation) and updates the session on username change.
- Tests use a temporary DB via the existing test fixtures (so your real `todos.db` is unaffected).
- The monitoring stack is intentionally minimal — it provides quick visibility (request rate, p95 latency, error rate) and is easy to extend.

Next steps (optional)
---------------------
- Add keyboard support (Escape to close) and aria-expanded toggling on the hamburger for better accessibility.
- Add floating labels for inputs if you prefer that UX instead of placeholders.
- Add CI jobs: run tests and a post-deploy smoke-check that curls `/health` and `/metrics`.
- Harden security: replace the demo `app.secret_key`, add CSRF protection, and rate-limit critical endpoints.

If you want, I can now:
- Create GitHub Actions workflows for CI (test + coverage) and CD (Docker push or Render deploy),
- Add the CI smoke-check step to validate `/health` and `/metrics` after deployment,
- Tweak visual styles (placeholder opacity, input heights) or implement floating labels.

Contact
-------
If anything looks off when you run the app/tests or you want the CI/CD config added, tell me which deployment target you prefer and I will add the workflow files next.
