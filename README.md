# Visitor Log API

A FastAPI service for registering visitors, recording checkouts, and searching the daily visitor log for a condominium guardhouse.

## Setup

Use Python 3.13. From the repository root, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the API

```bash
python -m uvicorn main:app
```

Open [interactive API documentation](http://127.0.0.1:8000/docs) to try the endpoints.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Check that the service is running |
| POST | `/visitors` | Register a visitor and record their check-in time |
| POST | `/visitors/{visitor_id}/checkout` | Record the checkout time for a visit |
| GET | `/visitors` | List today's visits, with optional exact-match filters for `unit_number` and `vehicle_plate` |

## Run the tests

```bash
python -m pytest -q
```

The tests cover duplicate vehicle check-ins, checking in again after checkout, and vehicle plate validation.

## Assumptions

- The service runs with one worker and stores visits in memory. Restarting the service clears the records.
- All timestamps and daily queries use Singapore time. The daily list includes overnight visitors who are still on site or checked out after midnight.
- Vehicle plates are optional. Supplied plates are converted to uppercase and spaces are removed before validation and duplicate checks.
- Plate validation covers the standard Singapore plate format and checksum. It does not verify that a plate has been issued.
- If both search filters are supplied, a visit must match both.