from sqlalchemy import Column, Integer, String
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    dob = Column(String)
    contact_email = Column(String, unique=True)
    contact_number = Column(String)
    contact_address = Column(String)
    education = Column(String)
    graduation_year = Column(Integer)
    experience = Column(Integer)
    skills = Column(String)
    resume_file = Column(String)
    created_at = Column(String)