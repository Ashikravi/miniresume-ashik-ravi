# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Response
from fastapi.responses import JSONResponse


app = FastAPI()

# In-memory storage
candidates = []
current_id = 1

UPLOAD_FOLDER = "uploads"
ALLOWED_EXT = (".pdf", ".doc", ".docx")


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