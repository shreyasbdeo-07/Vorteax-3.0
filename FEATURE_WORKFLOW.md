# VORTEXA assessment security and feature-lock workflow

## Unlock condition
1. Candidate has saved full name, email, phone, degree, branch, and college.
2. Candidate has selected at least one skill.
3. The latest attempt for every selected skill has status `COMPLETED`. A `TERMINATED` attempt does not satisfy the requirement.
4. The backend creates or reuses the Skill Passport record.
5. The UI unlocks the Skill Passport and personalized Job Match/Job Recommendations.

The backend is authoritative. UI locks are a visual layer; protected recommendation routes check passport eligibility independently. Editing the selected skill list invalidates an existing passport so newly selected skills cannot inherit verification.

## Proctoring caveats
Tab visibility and window-focus events are recorded as warnings. Fullscreen exits are recorded. Camera-based phone detection uses COCO-SSD and can miss phones or produce false positives; browser camera access and model loading are required. Proctoring is not tamper-proof.

## Local setup
See `README.md` and `backend/README.md`. Set up `backend/.env`, install `backend/requirements.txt`, apply `backend/migrate.py`, seed question bank, and run `backend/app.py`.
