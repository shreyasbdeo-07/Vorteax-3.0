# VORTEXA 3.0 backend — Local MySQL

See the project-root `README.md` for complete setup instructions.

Quick commands from this folder:
1. Edit `.env` and set your local MySQL password.
2. `py -m venv .venv`
3. `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. `python migrate.py`
6. `python database.py`
7. `python app.py`

Local defaults: `127.0.0.1:3306`, database `vorteax_db`, user `root`, SSL disabled.
Do not commit `.env`. Aiven requires different host/port settings and its CA certificate.
