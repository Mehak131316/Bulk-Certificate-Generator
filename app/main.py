from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os

from . import models, schemas, database, generator

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Bulk Certificate Generator API")

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")

@app.post("/api/jobs/", response_model=schemas.JobResponse)
def create_job(job_data: schemas.JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    db_job = models.GenerationJob()
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    for recipient in job_data.recipients:
        db_cert = models.Certificate(
            job_id=db_job.id,
            recipient_name=recipient.recipient_name,
            course_name=recipient.course_name
        )
        db.add(db_cert)
    
    db.commit()
    db.refresh(db_job)
    
    background_tasks.add_task(generator.process_job, db_job.id)
    
    return db_job

@app.get("/api/jobs/{job_id}", response_model=schemas.JobResponse)
def get_job_status(job_id: int, db: Session = Depends(database.get_db)):
    job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/certificates/{cert_id}")
def get_certificate(cert_id: int, db: Session = Depends(database.get_db)):
    cert = db.query(models.Certificate).filter(models.Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.status != models.CertificateStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Certificate generation is not successful")
        
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found")
        
    return FileResponse(
        path=cert.file_path, 
        filename=f"certificate_{cert.recipient_name.replace(' ', '_')}.pdf",
        media_type='application/pdf'
    )
