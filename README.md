## Python Version: 3.13.7
Tested on:
- Python 3.13.7
- macOS 26.3

 ## Dependencies
- FastAPI
- Uvicorn (ASGI server)
- python-multipart (for file uploads)

### Installation steps ###

### Step 1: Clone the Repository
```bash
git clone https://github.com/Ashikravi/miniresume-ashik-ravi.git
cd miniresume-ashik-ravi
```

### Step 2: Create a Virtual Environment (Recommended)
```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install fastapi uvicorn python-multipart
```

Or use `requirements.txt`: 
```bash
pip install -r requirements.txt
```

## Running the Application

### Using Uvicorn 
```bash
uvicorn main:app --reload
```
### Expected Output
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.

The application will be available at:
- **API Base URL:** `http://127.0.0.1:8000`
- **Interactive API Docs (Swagger):** `http://127.0.0.1:8000/docs`

# API Documentation

Once the application is running, visit `http://127.0.0.1:8000/docs` for interactive API documentation where you can test all endpoints.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/health` | Health check |
| POST | `/candidates` | Create a new candidate with resume upload |
| GET | `/candidates` | List all candidates with optional filters |
| GET | `/candidates/{id}` | Get specific candidate details |
| DELETE | `/candidates/{id}` | Delete a candidate |

---

##  Example Usage

### 1. Health Check

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Response:**
```json
{
  "status": "ok"
}
```

---

### 2. Create a New Candidate

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/candidates" \
  -F "full_name=John Doe" \
  -F "dob=1995-06-15" \
  -F "contact_email=john.doe@example.com" \
  -F "contact_number=+1234567890" \
  -F "contact_address=123 Main Street, New York, NY 10001" \
  -F "education=Bachelor of Technology in Computer Science" \
  -F "graduation_year=2017" \
  -F "experience=5" \
  -F "skills=Python, FastAPI, Docker, PostgreSQL" \
  -F "resume=@/path/to/resume.pdf"
```

**Response:**
```json
{
  "message": "Candidate created successfully",
  "id": 1
}
```

**Status Code:** `201 Created`

**Response Headers:**
```
Location: /candidates/1
```

---

### 3. List All Candidates

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/candidates"
```

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "John Doe",
    "graduation_year": 2017,
    "experience": 5,
    "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    "contact_email": "john.doe@example.com"
  },
  {
    "id": 2,
    "full_name": "Jane Smith",
    "graduation_year": 2019,
    "experience": 3,
    "skills": ["JavaScript", "React", "Node.js"],
    "contact_email": "jane.smith@example.com"
  }
]
```

**Status Code:** `200 OK`

---

### 4. Filter Candidates by Skill

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/candidates?skill=Python"
```

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "Alan J",
    "graduation_year": 2017,
    "experience": 5,
    "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    "contact_email": "Alan.j@example.com"
  }
]
```

---

### 5. Filter by Multiple Parameters

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/candidates?skill=Python&experience=5&graduation_year=2017"
```

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "John Doe",
    "graduation_year": 2017,
    "experience": 5,
    "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    "contact_email": "alan.je@example.com"
  }
]
```

---

### 6. Search by Name

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/candidates?name=John"
```

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "Alan J",
    "graduation_year": 2017,
    "experience": 5,
    "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    "contact_email": "john.doe@example.com"
  }
]
```

---

### 7. Get Candidate by ID

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/candidates/1"
```

**Response:**
```json
{
  "id": 1,
  "full_name": "Alan J",
  "dob": "1995-06-15",
  "contact_email": "alan.j@example.com",
  "contact_number": "+1234567890",
  "contact_address": "123 Main Street, New York, NY 10001",
  "education": "Bachelor of Technology in Computer Science",
  "graduation_year": 2017,
  "experience": 5,
  "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
  "resume_file": "uploads/a1b2c3d4e5f6.pdf",
  "created_at": "2024-02-15T10:30:00.123456+00:00"
}
```

**Status Code:** `200 OK`

---

### 8. Delete a Candidate

**Request:**
```bash
curl -X DELETE "http://127.0.0.1:8000/candidates/1"
```

**Response:**
```
(No content)
```

**Status Code:** `204 No Content`