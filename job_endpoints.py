"""
Little Lines — Job Queue Endpoints
Submit jobs and poll for results
"""
import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, File, Form, UploadFile
import redis as redis_lib

job_router = APIRouter(prefix="/job", tags=["jobs"])

def get_redis():
    """Get Redis connection"""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    if redis_url.startswith('rediss://'):
        return redis_lib.Redis.from_url(redis_url, ssl_cert_reqs=None)
    return redis_lib.Redis.from_url(redis_url)


def fix_flutterflow_json(body_str: str) -> dict:
    """
    FlutterFlow sends JSON objects as quoted strings inside the body.
    e.g. "character": "{"name":"Tim"}" instead of "character": {"name":"Tim"}
    
    This function tries json.loads first. If it fails, it fixes the quoted objects.
    """
    try:
        return json.loads(body_str)
    except json.JSONDecodeError:
        pass
    
    # Fix: find patterns like "key": "{...}" and unquote them
    import re
    
    # Replace "key": "{" with "key": { (opening)
    fixed = re.sub(r'(":\s*)"(\{)', r'\1\2', body_str)
    # Replace }"  with } at end of quoted objects (before comma or closing brace)
    fixed = re.sub(r'\}"(\s*[,\}])', r'}\1', fixed)
    # Fix escaped quotes inside the now-unquoted objects
    fixed = fixed.replace('\\"', '"')
    
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # Last resort: try to parse line by line
    # If nothing works, raise the error
    raise json.JSONDecodeError("Could not parse FlutterFlow JSON", body_str, 0)


@job_router.post("/submit")
async def submit_job(request: Request):
    """
    Submit a job to the queue. Returns job_id instantly.
    Handles FlutterFlow's quirky JSON serialization.
    """
    from celery_app import celery_app
    
    body = await request.body()
    body_str = body.decode('utf-8', errors='replace')
    
    try:
        params = fix_flutterflow_json(body_str)
    except Exception as e:
        print(f"[JOB-SUBMIT] JSON parse failed: {e}")
        print(f"[JOB-SUBMIT] Raw body: {body_str[:1000]}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    job_type = params.pop("job_type", "full_story")
    
    print(f"[JOB-SUBMIT] job_type: {job_type}")
    print(f"[JOB-SUBMIT] params keys: {list(params.keys())}")
    
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    r = get_redis()
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "job_type": job_type,
        "progress": None,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))
    
    task_map = {
        "extract_and_reveal": "tasks.extract_and_reveal_task",
        "character_reveal_flow": "tasks.character_reveal_flow_task",
        "full_story": "tasks.generate_full_story_task",
        "colouring_page": "tasks.generate_colouring_page_task",
        "storybook_pdf": "tasks.generate_storybook_pdf_task",
    }
    
    task_name = task_map.get(job_type)
    if not task_name:
        raise HTTPException(status_code=400, detail=f"Unknown job type: {job_type}")
    
    # Serialize params safely for Celery/Redis
    safe_params = json.loads(json.dumps(params, default=str))
    
    celery_app.send_task(task_name, args=[job_id, safe_params])
    
    return {"job_id": job_id, "status": "queued"}


@job_router.post("/submit-reveal")
async def submit_reveal_job(
    image: UploadFile = File(...),
    character_name: str = Form(...),
    age_level: str = Form("age_5"),
    has_second_character: str = Form("false"),
    second_character_name: str = Form(""),
    second_image: UploadFile = File(None),
    writing_style: str = Form(""),
    life_lesson: str = Form(""),
    custom_theme: str = Form(""),
    user_id: str = Form(""),
):
    """
    Submit a character reveal flow job via multipart form (for FlutterFlow).
    Accepts image as file upload, converts to base64, submits to Celery queue.
    Returns job_id instantly.
    """
    from celery_app import celery_app
    import base64
    
    # Upload main image to Firebase first (avoids sending large b64 through Redis)
    image_data = await image.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    
    from firebase_utils import upload_to_firebase
    temp_image_url = upload_to_firebase(image_b64, folder="adventure/temp-uploads")
    
    # Second image - read file and upload to Firebase if provided
    temp_second_url = ""
    if second_image:
        second_data = await second_image.read()
        if second_data and len(second_data) > 100:
            second_b64 = base64.b64encode(second_data).decode('utf-8')
            temp_second_url = upload_to_firebase(second_b64, folder="adventure/temp-uploads")
    
    # Clean FlutterFlow's "null" strings
    has_second = has_second_character.lower() in ("true", "1", "yes")
    writing_style_clean = writing_style if writing_style not in ["", "null", "None"] else None
    life_lesson_clean = life_lesson if life_lesson not in ["", "null", "None"] else None
    custom_theme_clean = custom_theme if custom_theme not in ["", "null", "None"] else None
    second_name_clean = second_character_name if second_character_name not in ["", "null", "None"] else ""
    
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    r = get_redis()
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "job_type": "character_reveal_flow",
        "progress": None,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    r.setex(f"job:{job_id}", 7200, json.dumps(job_data))  # 2 hour TTL for longer reveal jobs
    
    celery_app.send_task("tasks.character_reveal_flow_task", args=[job_id, {
        "image_url": temp_image_url,
        "character_name": character_name,
        "age_level": age_level,
        "has_second_character": has_second,
        "second_image_url": temp_second_url,
        "second_character_name": second_name_clean,
        "writing_style": writing_style_clean,
        "life_lesson": life_lesson_clean,
        "custom_theme": custom_theme_clean,
        "user_id": user_id,
    }])
    
    return {"job_id": job_id, "status": "queued"}


@job_router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    r = get_redis()
    job_raw = r.get(f"job:{job_id}")
    if not job_raw:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return json.loads(job_raw)


def update_job_status(job_id: str, status: str, progress: str = None, result: dict = None, error: str = None):
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
