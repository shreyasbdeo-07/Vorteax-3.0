# VORTEXA 3.0 — Candidate Profile, Skill Assessment and Skill Passport

## Included
- Flask login/register for Candidate and Company accounts with Werkzeug password hashing.
- Candidate profile API storing personal details, degree, branch, college, graduation year and skills in MySQL.
- Searchable-ready dropdown data for degree, branch and selected Pune colleges.
- Server-side assessment attempts with question randomization, hidden answer keys, a 15-minute time limit, server-side scoring, and attempt/result history.
- Skill Passport is issued only after every skill currently selected in the candidate profile has a completed assessment result.
- Existing candidate/company dashboard templates and original job dashboard JavaScript are retained, but job-related APIs not present in this package may still need integration.

## Windows setup
1. Install Python 3.11+ and MySQL 8.
2. Create a database and application user, or use your existing local MySQL credentials.
3. Copy `backend/.env.example` to `backend/.env` and edit the values locally. Never commit `.env`.
4. In MySQL Workbench, open and run `backend/schema.sql` while connected to your MySQL server. It creates the database tables only if missing and seeds skills and starter questions. Do not run against production before backing up your database.
5. Open PowerShell in this folder:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   python backend\app.py
   ```
6. Open `http://127.0.0.1:5000/auth`.

## AI-generated questions with Qwen2.5-Coder
1. Install Ollama for Windows.
2. Run `ollama pull qwen2.5-coder:7b` in PowerShell.
3. Keep Ollama running at `http://127.0.0.1:11434`.
4. Configure `OLLAMA_MODEL` and `OLLAMA_BASE_URL` in `backend/.env` if needed.
5. When a skill has fewer than 10 active questions, the app asks the local model for MCQs, validates the output, stores valid questions in MySQL, and randomizes the assessment. Answer keys stay server-side.

If Ollama is offline, existing questions are used; at least 3 active questions are required. AI-generated questions may contain mistakes, so review them before high-stakes hiring.

## Environment
Set DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSL_MODE, DB_SSL_CA, FLASK_SECRET_KEY. For Aiven, use the host/port/user/database supplied by Aiven, use its CA certificate, and set DB_SSL_MODE=verify_ca. Do not paste secrets into chat or commit them.

## Assessment behavior and limits
- Each selected skill needs at least 3 active questions. The supplied SQL seeds starter questions for Python, C++, SQL/MySQL, HTML and JavaScript. Add at least 3 questions per other skill before assessing it.
- The browser receives question text and choices only; answer keys remain server-side.
- The backend validates ownership and status and calculates the score itself. The 15-minute expiry is checked server-side at submission. Browser focus/fullscreen controls are not proof against all cheating.
- Passport issuance is based on completion of all skills selected in the profile, not a claim that the candidate's identity or skills were externally verified.

## Testing status
Source files were generated and Python syntax-checked. A live MySQL server and browser session were not available in this build environment, so database integration and end-to-end behavior must be tested on your computer before deployment.


## Database bootstrap
Run `Vorteax-3.0-database.sql` in MySQL Workbench to create/select `vorteax_db`, create tables, and seed starter skills/questions. It does not drop existing tables.


## Skill assessment setup (updated)
1. Copy `backend/.env.example` to `backend/.env` and enter your local MySQL credentials and a random `FLASK_SECRET_KEY`. Do not commit `.env`.
2. Run `cd backend` then `python migrate.py` to create the configured database and tables safely (it does not drop existing tables).
3. Run `python seed_assessments.py` to seed 30 questions per supported skill. The target exam uses 3 easy × 3 marks, 4 medium × 5 marks and 3 hard × 7 marks (50 total), with a 15-minute server-side time limit.
4. Start with `python app.py`. Saving the candidate profile redirects to `/assessments`.

Proctoring note: browsers cannot reliably prevent tab switching. This implementation records visibility/fullscreen changes and attempts browser-side face-count/mobile-object checks using BlazeFace and COCO-SSD. These detections can be wrong and are not a substitute for a supervised exam. Camera permission is requested only when the user starts an assessment; video is processed in-browser and is not uploaded by this code. TensorFlow model scripts are loaded from a CDN and need internet access.


## Skill verification and feature locks

- Candidate must save required profile details (including phone number) and select at least one skill.
- Each selected skill must have a latest assessment attempt with `COMPLETED` status. A terminated attempt does not count.
- The backend generates a Skill Passport only after these conditions are satisfied.
- Skill Passport and Job Match/Job Recommendations sections remain visibly locked before issuance.
- The recommendations and match APIs also enforce the passport check server-side (HTTP 423 while locked).
- Public job browsing and applications are separate from personalized recommendations.
- Assessment proctoring records tab/window focus changes and fullscreen exits. Camera-based face/phone detection depends on browser camera permission, lighting, device, and model loading; it is not a guarantee that every phone will be detected.

### Apply updates to an existing local database

From PowerShell in the project root:

```powershell
cd backend
py -3.13 migrate.py
py -3.13 seed_assessments.py
py -3.13 app.py
```

Configure `backend/.env` first using `backend/.env.example`. Do not upload `.env` or secrets to GitHub. The migration is designed to create missing tables, but always back up important data before applying schema changes.

### Verification notes

Python syntax compilation and JavaScript syntax checks are performed when packaging. End-to-end MySQL verification requires the recipient's own database credentials and data, so run the local setup and test the workflow in your environment.
