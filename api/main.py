import os
import uuid
import re
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job
from fastapi.staticfiles import StaticFiles

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
PROCESSED_DIR = "/app/processed"

redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(connection=redis_conn)

app = FastAPI()

app.mount("/downloads", StaticFiles(directory=PROCESSED_DIR), name="downloads")

def validate_timestamp(ts: str) -> bool:
    return bool(re.match(r'^\d{2}:\d{2}:\d{2}$', ts))

def sanitize_output_name(name: str) -> str:
    name = re.sub(r'[^\w\.-]', '', name)
    if not name.endswith('.mp4'):
        name += '.mp4'
    return name

class TrimRequest(BaseModel):
    input_url: str
    start: str
    end: str
    output_name: Optional[str] = None

class RemoveRequest(BaseModel):
    input_url: str
    remove_start: str
    remove_end: str
    output_name: Optional[str] = None

class AutoflipRequest(BaseModel):
    input_url: str
    aspect_ratio: str = "9:16"
    debug: bool = False
    output_name: Optional[str] = None

@app.post("/jobs/trim")
def enqueue_trim(req: TrimRequest):
    if not validate_timestamp(req.start) or not validate_timestamp(req.end):
        raise HTTPException(status_code=400, detail="Invalid timestamp format")
    output_name = req.output_name or f"trim_{uuid.uuid4()}.mp4"
    output_name = sanitize_output_name(output_name)
    job = queue.enqueue('tasks.process_trim', req.input_url, req.start, req.end, output_name, job_timeout=3600)
    return {"job_id": job.id, "status_url": f"{BASE_URL}/jobs/{job.id}"}

@app.post("/jobs/remove")
def enqueue_remove(req: RemoveRequest):
    if not validate_timestamp(req.remove_start) or not validate_timestamp(req.remove_end):
        raise HTTPException(status_code=400, detail="Invalid timestamp format")
    output_name = req.output_name or f"remove_{uuid.uuid4()}.mp4"
    output_name = sanitize_output_name(output_name)
    job = queue.enqueue('tasks.process_remove_segment', req.input_url, req.remove_start, req.remove_end, output_name, job_timeout=3600)
    return {"job_id": job.id, "status_url": f"{BASE_URL}/jobs/{job.id}"}

@app.post("/jobs/autoflip")
def enqueue_autoflip(req: AutoflipRequest):
    output_name = req.output_name or f"autoflip_{uuid.uuid4()}.mp4"
    output_name = sanitize_output_name(output_name)
    job = queue.enqueue('tasks.process_autoflip', req.input_url, req.aspect_ratio, req.debug, output_name, job_timeout=3600)
    return {"job_id": job.id, "status_url": f"{BASE_URL}/jobs/{job.id}"}

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        status = job.get_status()
        result = {
            "id": job_id,
            "status": status
        }
        if status == "finished":
            result["result_url"] = f"{BASE_URL}/downloads/{job.result}"
        elif status == "failed":
            result["error"] = str(job.exc_info) if job.exc_info else "Unknown error"
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail="Job not found")