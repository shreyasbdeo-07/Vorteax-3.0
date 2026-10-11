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


### Skill assessments
Run `python migrate.py`, then `python seed_assessments.py`. The seed script provides 30 fixed MCQs for every catalog skill, grouped by difficulty. Python and SQL have dedicated questions; other tracks currently use the shared technical fundamentals bank with skill-context wording and should be reviewed/customized before real hiring decisions. Every test randomly chooses 3 easy, 4 medium, and 3 hard questions for 50 marks total.
