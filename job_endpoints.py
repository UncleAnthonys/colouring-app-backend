"""
Little Lines — Job Queue Endpoints
Submit jobs and poll for results
"""
import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import redis as redis_lib

job_router = APIRouter(prefix="/job", tags=["jobs"])

def get_redis():
    """Get Redis connection"""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    if redis_url.startswith('rediss://'):
        return redis_lib.Redis.from_url(redis_url, ssl_cert_reqs=None)
    return redis_lib.Redis.from_url(redis_url)


class JobSubmitRequest(BaseModel):
    job_type: str  # "extract_and_reveal", "full_story", "colouring_page", "storybook_pdf"
    params: Dict[str, Any]


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "processing", "complete", "failed"
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@job_router.post("/submit")
async def submit_job(request: JobSubmitRequest):
    """
    Submit a job to the queue. Returns job_id instantly.
    FlutterFlow then polls /job/{job_id}/status for results.
    """
    from celery_app import celery_app
    
    # Debug: log what was sent
    print(f"[JOB-SUBMIT] job_type: {request.job_type}")
    if request.params:
        for k, v in request.params.items():
            val_type = type(v).__name__
            val_preview = str(v)[:100] if v is not None else "None"
            print(f"[JOB-SUBMIT]   {k} ({val_type}): {val_preview}")
    
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Store initial job status in Redis
    r = get_redis()
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "job_type": request.job_type,
        "progress": None,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))  # Expires in 1 hour
    
    # Map job types to Celery tasks
    task_map = {
        "extract_and_reveal": "tasks.extract_and_reveal_task",
        "full_story": "tasks.generate_full_story_task",
        "colouring_page": "tasks.generate_colouring_page_task",
        "storybook_pdf": "tasks.generate_storybook_pdf_task",
    }
    
    task_name = task_map.get(request.job_type)
    if not task_name:
        raise HTTPException(status_code=400, detail=f"Unknown job type: {request.job_type}")
    
    # Send task to Celery queue
    celery_app.send_task(task_name, args=[job_id, request.params])
    
    return {"job_id": job_id, "status": "queued"}


@job_router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Poll for job status. Returns current status + result when complete.
    """
    r = get_redis()
    job_raw = r.get(f"job:{job_id}")
    
    if not job_raw:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    
    job_data = json.loads(job_raw)
    return JobStatusResponse(**job_data)


def update_job_status(job_id: str, status: str, progress: str = None, result: dict = None, error: str = None):
    """
    Helper for tasks to update job status in Redis.
    Called from within Celery tasks.
    """
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    if redis_url.startswith('rediss://'):
        r = redis_lib.Redis.from_url(redis_url, ssl_cert_reqs=None)
    else:
        r = redis_lib.Redis.from_url(redis_url)
    
    job_raw = r.get(f"job:{job_id}")
    if job_raw:
        job_data = json.loads(job_raw)
    else:
        job_data = {"job_id": job_id}
    
    job_data["status"] = status
    job_data["updated_at"] = datetime.utcnow().isoformat()
    
    if progress is not None:
        job_data["progress"] = progress
    if result is not None:
        job_data["result"] = result
    if error is not None:
        job_data["error"] = error
    
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))
