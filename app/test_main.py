from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
import time

from .main import app
from .database import Base, get_db
from . import database

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the global session maker so the background task uses the test DB
database.SessionLocal = TestingSessionLocal

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_job():
    response = client.post(
        "/api/jobs/",
        json={"recipients": [{"recipient_name": "John Doe", "course_name": "Python 101"}]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert len(data["certificates"]) == 1
    assert data["certificates"][0]["recipient_name"] == "John Doe"

def test_input_validation():
    # Test empty recipients list
    response = client.post(
        "/api/jobs/",
        json={"recipients": []}
    )
    assert response.status_code == 422 
    
    # Test missing fields
    response = client.post(
        "/api/jobs/",
        json={"recipients": [{"recipient_name": ""}]} 
    )
    assert response.status_code == 422

def test_certificate_generation_and_status():
    response = client.post(
        "/api/jobs/",
        json={"recipients": [{"recipient_name": "Alice Smith", "course_name": "FastAPI"}]}
    )
    job_id = response.json()["id"]
    
    # Allow a little time for the background task to run
    time.sleep(1)
    
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["certificates"][0]["status"] == "SUCCESS"
    
def test_certificate_failure():
    # Sending 'fail_test' triggers a simulated exception in generator.py
    response = client.post(
        "/api/jobs/",
        json={"recipients": [
            {"recipient_name": "fail_test", "course_name": "Error 101"},
            {"recipient_name": "Bob Jones", "course_name": "Success 101"}
        ]}
    )
    job_id = response.json()["id"]
    
    time.sleep(1)
    
    response = client.get(f"/api/jobs/{job_id}")
    data = response.json()
    
    assert data["status"] == "COMPLETED"
    assert len(data["certificates"]) == 2
    
    # First should fail, second should succeed to show bulk processes continue
    assert data["certificates"][0]["status"] == "FAILED"
    assert data["certificates"][0]["error_message"] == "Simulated failure for testing"
    assert data["certificates"][1]["status"] == "SUCCESS"

def test_retrieve_certificate():
    response = client.post(
        "/api/jobs/",
        json={"recipients": [{"recipient_name": "Charlie", "course_name": "Retrieve Course"}]}
    )
    job_id = response.json()["id"]
    
    time.sleep(1)
    
    # Get job to find certificate ID
    response = client.get(f"/api/jobs/{job_id}")
    cert_id = response.json()["certificates"][0]["id"]
    
    # Retrieve file
    cert_response = client.get(f"/api/certificates/{cert_id}")
    assert cert_response.status_code == 200
    assert cert_response.headers["content-type"] == "application/pdf"
