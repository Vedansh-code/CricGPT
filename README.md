# CricGPT API Backend Service

Production-quality FastAPI backend service layer over the CricGPT Cricket Analytics SDK. 

## Features

- **Direct SDK Integration**: The API layer serves as a thin wrapper over the CricGPT Analytics SDK without duplicating SQL query logic.
- **Robust Exception Handling**: Custom SDK exceptions like `PlayerNotFoundError` are mapped to standard HTTP statuses (e.g., `404 Not Found`, `409 Conflict` for ambiguities).
- **Comprehensive API Routes**: Over 15 endpoints covering Player Profiles/Stats, Batting, Bowling, Matchups, Team records, Venues, and Matches.
- **Configurable CORS**: Supports safe local development and custom domains via environment configurations.

## Installation

1. Install dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set the SQLite Database path environment variable if not using the default location:
   - On Windows (Command Prompt):
     ```cmd
     set CRICGPT_DB_PATH=data\database\cricgpt.db
     ```
   - On Windows (PowerShell):
     ```powershell
     $env:CRICGPT_DB_PATH="data/database/cricgpt.db"
     ```

3. (Optional) Configure CORS allowed origins:
   ```cmd
   set CRICGPT_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

## Starting the API

Run the FastAPI application locally using uvicorn:
```bash
python -m uvicorn api.main:app --reload
```

By default, the server runs on `http://127.0.0.1:8000`.

- **Swagger Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Running Tests

To run the unified test suite containing both Phase 1 SDK tests and Phase 2 API tests:
```bash
python -m unittest discover -s tests
```

## Running the Demo Script

Start the server in one terminal and execute the demo script in another to see sample outputs for 12 key scenarios:
```bash
python demo_api.py
```
