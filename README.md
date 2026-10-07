# Bulk Certificate Generator

A backend API for generating course completion certificates in bulk. 
Built with Python, FastAPI, and SQLite.

## Design Decisions

- **Framework**: FastAPI was chosen for its excellent performance, automatic Swagger UI documentation, built-in validation (Pydantic), and simplicity in handling background tasks.
- **Database**: SQLite with SQLAlchemy ORM. SQLite is used for ease of setup and portability for this assignment, but SQLAlchemy makes it trivial to swap for PostgreSQL or MySQL in production.
- **Bulk Processing**: Handled asynchronously using FastAPI's built-in `BackgroundTasks`. This allows the API to return immediately with a job ID while certificates are generated in the background. It avoids blocking HTTP requests for large batches.
- **Certificate Generation**: Uses `fpdf2` to generate PDF files directly. A single predefined template layout is hardcoded in `generator.py`.
- **Failure Handling**: The generation loop uses a `try/except` block for each certificate. If one fails, its status is marked as `FAILED` with the error message recorded, but the rest of the job continues processing.

## Setup Instructions

1. **Create and activate a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the FastAPI development server from the root directory:
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.
You can access the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Running Tests

Tests are written using `pytest`. To run them, execute:
```bash
pytest app/test_main.py -v
```

## API Usage

### 1. Submit a Certificate Generation Request

Send a `POST` request to `/api/jobs/` with a list of recipients.

**Request:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/jobs/' \
  -H 'Content-Type: application/json' \
  -d '{
  "recipients": [
    {
      "recipient_name": "Jane Doe",
      "course_name": "Advanced Python"
    },
    {
      "recipient_name": "John Smith",
      "course_name": "FastAPI Masterclass"
    }
  ]
}'
```

**Response:**
```json
{
  "id": 1,
  "status": "PENDING",
  "created_at": "2023-10-27T10:00:00",
  "certificates": [
    {
      "id": 1,
      "recipient_name": "Jane Doe",
      "course_name": "Advanced Python",
      "status": "PENDING",
      "error_message": null
    }
  ]
}
```

### 2. Check Job Status

Send a `GET` request to `/api/jobs/{job_id}` to check progress.

**Request:**
```bash
curl -X 'GET' 'http://127.0.0.1:8000/api/jobs/1'
```

### 3. Retrieve Generated Certificates

Once a certificate status is `SUCCESS`, use its ID to download the PDF.

**Request:**
```bash
curl -X 'GET' -O -J 'http://127.0.0.1:8000/api/certificates/1'
```
This will download the certificate as a PDF file.
