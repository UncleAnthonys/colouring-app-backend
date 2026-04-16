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
        "sketch": "tasks.generate_sketch_task",
        "storybook_pdf": "tasks.generate_storybook_pdf_task",
        "pack": "tasks.generate_pack_task",
    }
    
    task_name = task_map.get(job_type)
    if not task_name:
        raise HTTPException(status_code=400, detail=f"Unknown job type: {job_type}")
    
    # Serialize params safely for Celery/Redis
    safe_params = json.loads(json.dumps(params, default=str))
    
    # For pack jobs, look up subjects server-side so frontend only sends pack_id
    if job_type == "pack":
        from pack_config import PACK_CATALOG
        pack_id = safe_params.get("pack_id")
        pack_def = PACK_CATALOG.get(pack_id)
        if not pack_def:
            raise HTTPException(status_code=400, detail=f"Unknown pack_id: {pack_id}")
        safe_params["pack_name"] = pack_def["name"]
        safe_params["subjects"] = pack_def["subjects"]
    
    celery_app.send_task(task_name, args=[job_id, safe_params])
    
    return {"job_id": job_id, "status": "queued"}


@job_router.post("/submit-reveal")
async def submit_reveal_job(request: Request):
    """
    Submit a SINGLE character extract+reveal job.
    Accepts multipart form with image file upload.
    Uploads image to Firebase first, passes URL to worker (avoids Redis size limits).
    Returns job_id instantly — poll /job/{id}/status for result.
    
    Result contains: character, reveal_description, reveal_image_url, source_type
    (Same data as the old /extract-and-reveal endpoint, just queued)
    """
    from celery_app import celery_app
    import base64
    from firebase_utils import upload_to_firebase
    
    form = await request.form()
    
    image = form.get("image")
    character_name = form.get("character_name", "Character")
    user_id = form.get("user_id", "")
    
    if not image or not hasattr(image, 'read'):
        raise HTTPException(status_code=400, detail="No image file provided")
    
    # Upload image to Firebase (avoids sending large b64 through Redis)
    image_data = await image.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    temp_image_url = upload_to_firebase(image_b64, folder="adventure/temp-uploads")
    
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    r = get_redis()
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "job_type": "extract_and_reveal",
        "progress": None,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))
    
    celery_app.send_task("tasks.extract_and_reveal_task", args=[job_id, {
        "image_url": temp_image_url,
        "character_name": character_name,
        "user_id": user_id,
    }])
    
    return {"job_id": job_id, "status": "queued"}


@job_router.post("/submit-reveal-second")
async def submit_reveal_second_job(request: Request):
    """
    Submit a SECOND character extract+reveal job.
    Same as /submit-reveal but for the companion character.
    Accepts multipart form with image file upload.
    """
    from celery_app import celery_app
    import base64
    from firebase_utils import upload_to_firebase
    
    form = await request.form()
    
    image = form.get("image")
    character_name = form.get("character_name", "Character")
    user_id = form.get("user_id", "")
    
    if not image or not hasattr(image, 'read'):
        raise HTTPException(status_code=400, detail="No image file provided")
    
    # Upload image to Firebase
    image_data = await image.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    temp_image_url = upload_to_firebase(image_b64, folder="adventure/temp-uploads")
    
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    r = get_redis()
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "job_type": "extract_and_reveal",
        "progress": None,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))
    
    celery_app.send_task("tasks.extract_and_reveal_task", args=[job_id, {
        "image_url": temp_image_url,
        "character_name": character_name,
        "user_id": user_id,
        "is_second_character": True,
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


# --- Pack Catalog ---

@job_router.get("/packs/catalog")
async def get_pack_catalog():
    """
    Return all available colouring page packs with metadata.
    Frontend calls this to populate the pack browsing UI.
    Endpoint: GET /job/packs/catalog
    """
    from pack_config import PACK_CATALOG

    catalog = []
    for pack_id, pack_def in PACK_CATALOG.items():
        catalog.append({
            "pack_id": pack_id,
            "name": pack_def["name"],
            "description": pack_def["description"],
            "page_count": len(pack_def["subjects"]),
            "subjects": pack_def["subjects"],
            "category": pack_def.get("category", "general"),
            "cover_emoji": pack_def.get("cover_emoji", "🎨"),
            "subjects_display": ", ".join(pack_def.get("display_names", pack_def["subjects"])),
        })
    return {"packs": catalog}
