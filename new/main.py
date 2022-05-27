from fastapi import FastAPI, Depends
from schemas import CreateJobRequest
from sqlalchemy.orm import Session
from database import get_db
from models import Job

app= FastAPI()
@app.post("/")
def create_job(job: CreateJobRequest, db: Session = Depends(get_db)):
    new_job = Job(title=job.title, description=job.description)
    db.add(new_job)
    db.commit()
    # db.refresh(new_job)
    return {"success": True, "created_id": new_job.id}