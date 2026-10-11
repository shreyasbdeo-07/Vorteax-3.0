# Assessment fix notes

This package includes a fix for assessment start failing when MySQL returns difficulty enum values in lowercase (`easy`, `medium`, `hard`). The backend now normalizes the value to uppercase before assigning the required marks (3/5/7).

## Setup / run (Windows)

1. Extract this folder.
2. Configure `backend/.env` using `backend/.env.example` and your local MySQL credentials. Do not share or commit your `.env` file.
3. From the project root, install backend dependencies:

   ```powershell
   py -3.13 -m pip install -r backend/requirements.txt
   ```

4. Run the database migration from the backend directory:

   ```powershell
   cd backend
   py -3.13 migrate.py
   py -3.13 seed_assessments.py
   py -3.13 app.py
   ```

5. Open `http://127.0.0.1:5000`.

The migration is intended to be repeatable and does not drop existing tables. Existing database credentials and selected skills still need to be valid for the app to run correctly.
