from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
import shutil
import os
from uuid import uuid4
from datetime import datetime, date, timezone
import re

app = FastAPI()

# In-memory storage
candidates = [] #candidates database
current_id = 1 

UPLOAD_FOLDER = "uploads"
ALLOWED_EXT = (".pdf", ".doc", ".docx")

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


def validate_email(email: str) -> bool:
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone)
    return  7 <= len(digits) <= 15


def validate_dob(dob_str: str) -> date:
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="DOB must be in YYYY-MM-DD format")
    if dob >= date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="DOB must be a past date")
    return dob


# Health Check
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

#Root endpoint
@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {
        "message": "Welcome to Mini Resume Management API",
        "total_candidates": len(candidates),
        "docs": "/docs",
        "health": "/health"
    }

# Upload Candidate Resume

@app.post("/candidates", status_code=status.HTTP_201_CREATED)
def create_candidate(
    full_name: str = Form(...),
    dob: str = Form(...),  # YYYY-MM-DD
    contact_email: str = Form(...),
    contact_number: str = Form(...),
    contact_address: str = Form(...),
    education: str = Form(...),
    graduation_year: int = Form(...),
    experience: int = Form(..., ge=0),
    skills: str = Form(...),  # comma separated
    resume: UploadFile = File(...)
):
    
    """
    
    Create a candidate entry with metadata and uploaded resume file.
    DOB must be YYYY-MM-DD.
    Email and phone are validated.
    Skills are provided as comma-separated string.
    MAX_FILE_SIZE for resume < 10mb
    
    """
    global current_id

    # Validate contact email and phone and dob
    if not validate_email(contact_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid email format")

    if not validate_phone(contact_number):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid contact number (must contain 7-15 digits)")

    _ = validate_dob(dob)

    # Validate filename presence and file type
    filename = resume.filename

    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    if not filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    #File size validation 
    resume.file.seek(0, 2)
    file_size = resume.file.tell()
    resume.file.seek(0)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size must be less than 10MB")

    # Ensure upload folder
    ensure_upload_folder()

    # Save file with a unique name 
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to save uploaded file")

    skill_list = [s.strip() for s in skills.split(",") if s.strip()]

    candidate = {
        "id": current_id,
        "full_name": full_name,
        "dob": dob,
        "contact_email": contact_email,
        "contact_number": contact_number,
        "contact_address": contact_address,
        "education": education,
        "graduation_year": graduation_year,
        "experience": experience,
        "skills": skill_list,
        "resume_file": file_path,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    candidates.append(candidate)
    created_id = current_id
    current_id += 1

    # Return 201 Created with Location header pointing to the new resource
    headers = {"Location": f"/candidates/{created_id}"}
    return JSONResponse(status_code=status.HTTP_201_CREATED,
                        content={"message": "Candidate created successfully", "id": created_id},
                        headers=headers)


# List and Filter Candidates 

@app.get("/candidates", status_code=status.HTTP_200_OK)
def list_candidates(
    skill: Optional[str] = None,
    experience: Optional[int] = None,
    graduation_year: Optional[int] = None,
    name: Optional[str] = None
):
    results = candidates

    if skill:
        skill_lower = skill.lower()
        results = [c for c in results if any(s.lower() == skill_lower for s in c["skills"])]

    if experience is not None:
        results = [c for c in results if c["experience"] == experience]

    if graduation_year is not None:
        results = [c for c in results if c["graduation_year"] == graduation_year]

    if name:
        name_lower = name.lower()
        results = [c for c in results if name_lower in c["full_name"].lower()]

    # Return lightweight items for list view
    return [dict(
        id=c["id"],
        full_name=c["full_name"],
        graduation_year=c["graduation_year"],
        experience=c["experience"],
        skills=c["skills"],
        contact_email=c["contact_email"]
    ) for c in results]


# Get Candidate by ID

@app.get("/candidates/{candidate_id}", status_code=status.HTTP_200_OK)
def get_candidate(candidate_id: int):
    for candidate in candidates:
        if candidate["id"] == candidate_id:
            return candidate
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

# Delete Candidate

@app.delete("/candidates/{candidate_id}",)
def delete_candidate(candidate_id: int):
    """
    Delete candidate and saved resume file.
    Returns 204 No Content on success.
    """
    global candidates

    for candidate in candidates:
        if candidate["id"] == candidate_id:
            # attempt to remove file (best-effort)
            try:
                if os.path.exists(candidate["resume_file"]):
                    os.remove(candidate["resume_file"])
            except Exception:
                pass

            candidates = [c for c in candidates if c["id"] != candidate_id]
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

