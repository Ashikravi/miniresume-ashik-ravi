from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Response, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import shutil
import os
from uuid import uuid4
from datetime import datetime, date, timezone
import re
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models 


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_FOLDER = "uploads"
ALLOWED_EXT = (".pdf", ".doc", ".docx")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

#Validations
def validate_email(email: str):
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    if not re.match(pattern, email):
        raise HTTPException(status_code=400,detail="Invalid email format")


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
def root(db: Session = Depends(get_db)):
    total = db.query(models.Candidate).count()
    return {
        "message": "Welcome to Mini Resume Management API",
        "total_candidates": total,
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
    graduation_year: int = Form(..., ge=2010, le=datetime.now().year + 1),
    experience: int = Form(..., ge=0),
    skills: str = Form(...),  # comma separated
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    
    """
    
    Create a candidate entry with metadata and uploaded resume file.
    DOB must be YYYY-MM-DD.
    Email and phone are validated.
    Skills are provided as comma-separated string.
    MAX_FILE_SIZE for resume < 10mb
    
    """

    # Validate contact email and phone and dob
    validate_email(contact_email)

    #if email is existing
    existing = db.query(models.Candidate).filter(
        models.Candidate.contact_email == contact_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    if not validate_phone(contact_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contact number"
        )

    _ = validate_dob(dob)

    # Validate filename presence and file type
    filename = resume.filename

    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    if not filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(status_code=400, detail="Invalid file type! Only PDF, DOC, DOCX files are allowed for resume")
    
    #File size validation 
    resume.file.seek(0, 2)
    file_size = resume.file.tell()
    resume.file.seek(0)
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
    if not skill_list:
        raise HTTPException(status_code=400, detail="At least one skill is required")

    candidate = models.Candidate(
        full_name=full_name,
        dob=dob,
        contact_email=contact_email,
        contact_number=contact_number,
        contact_address=contact_address,
        education=education,
        graduation_year=graduation_year,
        experience=experience,
        skills=",".join(skill_list),
        resume_file=file_path,
        created_at=datetime.now(timezone.utc).isoformat()
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Return 201 Created with Location header pointing to the new resource
    headers = {"Location": f"/candidates/{candidate.id}"}
    return JSONResponse(status_code=status.HTTP_201_CREATED,  content={
            "message": "Candidate created successfully",
            "id": candidate.id
        },
        headers=headers
    )


# List and Filter Candidates 

@app.get("/candidates", status_code=status.HTTP_200_OK)
def list_candidates(
    skill: Optional[str] = None,
    experience: Optional[int] = None,
    graduation_year: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Candidate)

    if skill:
        query = query.filter(models.Candidate.skills.ilike(f"%{skill}%"))

    if experience is not None:
        query = query.filter(models.Candidate.experience == experience)

    if graduation_year is not None:
        query = query.filter(models.Candidate.graduation_year == graduation_year)

    if name:
        query = query.filter(models.Candidate.full_name.ilike(f"%{name}%"))

    results = query.all()


    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "graduation_year": c.graduation_year,
            "experience": c.experience,
            "skills": c.skills.split(","),
            "contact_email": c.contact_email
        }
        for c in results
    ]


# Get Candidate by ID

@app.get("/candidates/{candidate_id}", status_code=status.HTTP_200_OK)
def get_candidate(candidate_id: int,  db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "dob": candidate.dob,
        "contact_email": candidate.contact_email,
        "contact_number": candidate.contact_number,
        "contact_address": candidate.contact_address,
        "education": candidate.education,
        "graduation_year": candidate.graduation_year,
        "experience": candidate.experience,
        "skills": candidate.skills.split(","),
        "resume_file": candidate.resume_file,
        "created_at": candidate.created_at
    }


# Delete Candidate
@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int, db:Session= Depends(get_db)):
    """
    Delete candidate and saved resume file.
    Returns 204 No Content on success.
    """
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    #delete uploaded resume_file
    try:
        if os.path.exists(candidate.resume_file):
            os.remove(candidate.resume_file)
    except Exception:
        pass

    db.delete(candidate)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
