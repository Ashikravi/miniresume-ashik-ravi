import re , os
from datetime import datetime, date
from fastapi import HTTPException, status

UPLOAD_FOLDER = "uploads"
def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # Ensure upload folder is existing or created.
ensure_upload_folder()

#Validations
def validate_email(email: str):
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    if not re.match(pattern, email):
        raise HTTPException(status_code=400,detail="Invalid email format")

def validate_phone(phone: str):
    pattern = r"^\+?\d{7,15}$"

    if not re.fullmatch(pattern, phone):
        raise HTTPException(
            status_code=400,
            detail="Invalid contact number!"
        )


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