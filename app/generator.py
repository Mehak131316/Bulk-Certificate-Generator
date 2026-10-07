import os
from fpdf import FPDF
from . import models
from .database import SessionLocal

OUTPUT_DIR = "generated_certificates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_certificate_pdf(recipient_name: str, course_name: str, filename: str):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Border
    pdf.set_line_width(2)
    pdf.rect(10, 10, 277, 190)
    
    # Title
    pdf.set_font('Helvetica', 'B', 32)
    pdf.cell(0, 40, 'Certificate of Completion', ln=True, align='C')
    
    # Subtitle
    pdf.set_font('Helvetica', '', 20)
    pdf.cell(0, 30, 'This is to certify that', ln=True, align='C')
    
    # Name
    pdf.set_font('Helvetica', 'B', 30)
    pdf.cell(0, 30, recipient_name, ln=True, align='C')
    
    # Course
    pdf.set_font('Helvetica', '', 20)
    pdf.cell(0, 20, 'has successfully completed the course', ln=True, align='C')
    
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 30, course_name, ln=True, align='C')
    
    pdf.output(filename)

def process_job(job_id: int):
    # Retrieve a session. Using SessionLocal allows us to override it in tests
    from . import database
    db = database.SessionLocal()
    try:
        job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
        if not job:
            return
        
        job.status = models.JobStatus.PROCESSING
        db.commit()
        
        for cert in job.certificates:
            try:
                # Support simulating a failure for testing purposes
                if cert.recipient_name.lower() == "fail_test":
                    raise Exception("Simulated failure for testing")
                    
                filename = os.path.join(OUTPUT_DIR, f"cert_{cert.id}.pdf")
                create_certificate_pdf(cert.recipient_name, cert.course_name, filename)
                
                cert.status = models.CertificateStatus.SUCCESS
                cert.file_path = filename
            except Exception as e:
                cert.status = models.CertificateStatus.FAILED
                cert.error_message = str(e)
            db.commit()
            
        job.status = models.JobStatus.COMPLETED
        db.commit()
    finally:
        db.close()
