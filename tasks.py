"""
Little Lines — Celery Tasks
Heavy AI generation work that runs on workers, not the API server.
"""
import os
import sys
import json
import asyncio
import traceback

# Ensure source directory is in Python path (fixes Render worker imports)
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from celery_app import celery_app
from job_endpoints import update_job_status

# Debug: log on import
print(f"[TASKS] Loaded from: {os.path.abspath(__file__)}")
print(f"[TASKS] CWD: {os.getcwd()}")
print(f"[TASKS] sys.path[0]: {sys.path[0]}")
print(f"[TASKS] .py files in src_dir: {[f for f in os.listdir(src_dir) if 'character' in f.lower()]}")


def run_async(coro):
    """Helper to run async functions from sync Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name='tasks.generate_full_story_task', bind=True, acks_late=True, reject_on_worker_lost=True)
def generate_full_story_task(self, job_id: str, params: dict):
    """
    Generate a complete storybook: story text + cover + 5 episode images + PDF.
    This is the heaviest operation (~3-5 minutes).
    """
    try:
        update_job_status(job_id, "processing", progress="Starting story generation...")
        
        # Force path fix inside task
        import sys, os
        task_dir = os.path.dirname(os.path.abspath(__file__))
        if task_dir not in sys.path:
            sys.path.insert(0, task_dir)
        
        # Import here to avoid circular imports and ensure env vars are loaded
        from adventure_gemini import (
            generate_adventure_episode_gemini,
            create_a4_page_with_text,
            create_front_cover,
            validate_episode_image
        )
        from gemini_story_engine import generate_story_gemini
        from adventure_config import get_age_rules
        from firebase_utils import upload_to_firebase
        from adventure_config import ADVENTURE_THEMES
        from app import normalize_age_level
        
        # Extract params — snake_case names matching generateFullStory endpoint exactly
        character_json = params.get("character", {})
        if isinstance(character_json, str):
            try:
                import json as json_mod
                character_json = json_mod.loads(character_json)
            except:
                character_json = {}
        
        character_name = character_json.get("name", "Character")
        character_description = params.get("character_description", character_json.get("description", ""))
        character_key_feature = character_json.get("key_feature", params.get("feature_used", ""))
        theme_name = params.get("theme_name", "")
        theme_description = params.get("theme_description", "")
        theme_blurb = params.get("theme_blurb", "")
        feature_used = params.get("feature_used", "")
        want = params.get("want", "")
        obstacle = params.get("obstacle", "")
        twist = params.get("twist", "")
        age_level = normalize_age_level(params.get("age_level", "age_5"))
        print(f"[STORY-TASK] raw: {params.get('age_level')}, normalized: {age_level}")
        writing_style = params.get("writing_style")
        life_lesson = params.get("life_lesson")
        custom_theme = params.get("custom_theme")
        
        # FlutterFlow sends literal "null" strings instead of actual null
        if writing_style in [None, "null", "", "None"]:
            writing_style = None
        if life_lesson in [None, "null", "", "None"]:
            life_lesson = None
        if custom_theme in [None, "null", "", "None"]:
            custom_theme = None
        reveal_image_b64 = params.get("reveal_image_b64")
        reveal_image_url = params.get("reveal_image_url")
        source_type = params.get("source_type", "drawing")
        
        # Download reveal from URL if b64 not provided (keeps Redis payload small)
        print(f"[WORKER] reveal_image_b64 length: {len(reveal_image_b64) if reveal_image_b64 else 0}")
        print(f"[WORKER] reveal_image_url: {reveal_image_url}")
        if reveal_image_url and not reveal_image_b64:
            try:
                import httpx
                resp = httpx.get(reveal_image_url, timeout=30)
                if resp.status_code == 200:
                    import base64 as b64mod
                    reveal_image_b64 = b64mod.b64encode(resp.content).decode('utf-8')
                    print(f"[WORKER] Downloaded reveal from URL, b64 length: {len(reveal_image_b64)}")
            except Exception as e:
                print(f"[WORKER] Failed to download reveal URL: {e}")
        second_character_name = params.get("second_character_name")
        second_character_description = params.get("second_character_description")
        second_character_image_b64 = params.get("second_character_image_b64")
        second_character_image_url = params.get("second_character_image_url")
        
        # Download second character from URL if b64 not provided
        if second_character_image_url and not second_character_image_b64:
            try:
                import httpx
                resp = httpx.get(second_character_image_url, timeout=30)
                if resp.status_code == 200:
                    import base64 as b64mod
                    second_character_image_b64 = b64mod.b64encode(resp.content).decode('utf-8')
                    print(f"[WORKER] Downloaded second character from URL")
            except Exception as e:
                print(f"[WORKER] Failed to download second character URL: {e}")
        
        # Get age rules
        age_rules = get_age_rules(age_level)
        
        # === STEP 1: Generate story text with Gemini ===
        update_job_status(job_id, "processing", progress="Writing your story...")
        
        story_data = generate_story_gemini(
            character_name=character_name,
            character_description=character_description,
            theme_name=theme_name,
            theme_description=theme_description,
            theme_blurb=theme_blurb,
            feature_used=feature_used,
            want=want,
            obstacle=obstacle,
            twist=twist,
            age_level=age_level,
            writing_style=writing_style,
            life_lesson=life_lesson,
            custom_theme=custom_theme,
            second_character_name=second_character_name,
            second_character_description=second_character_description,
        )
        
        episodes = story_data.get("episodes", [])
        story_title = story_data.get("story_title", f"{character_name}'s Adventure")
        full_title = f"{character_name} and {theme_name}" if not story_title.startswith(character_name) else story_title
        
        print(f"[WORKER] Story generated: {full_title}, {len(episodes)} episodes")
        
        # === STEP 2: Generate front cover ===
        update_job_status(job_id, "processing", progress="Creating your front cover...")
        
        cover_description = theme_description or theme_blurb or custom_theme or theme_name or ""
        
        cover_scene = f"""Create a CHILDREN'S COLORING BOOK FRONT COVER.

This is a FULL PAGE book cover that must include:

DO NOT include ANY text, words, letters, or writing in the image. NO TITLE. NO TEXT AT ALL. Text will be added separately by code.

IMAGE:
- {character_name} large and central, looking excited and confident
- Background hints at the adventure: {cover_description}
- Dynamic, eye-catching composition
- BLACK AND WHITE LINE ART suitable for coloring in
- Portrait orientation, fills the entire page

⚠️ NO BORDER - CRITICAL:
- There must be NO border, NO frame, NO outline, NO decorative edge around the image
- NO thin black line around the edge
- NO thick black line around the edge
- The artwork fades into white at the edges - no hard line boundary

⚠️ COMPOSITION:
- Character's HEAD must be in the MIDDLE of the image, NOT near the top
- TOP 30% must be completely empty — just plain white or simple sky. NOTHING ELSE
- All characters and objects in the LOWER 65% of the image

Make it look like a real children's coloring book cover you'd see in a shop!
"""
        
        cover_image_b64 = run_async(generate_adventure_episode_gemini(
            character_data={"name": character_name, "description": character_description, "key_feature": character_key_feature},
            scene_prompt=cover_scene,
            age_rules=age_rules["rules"],
            reveal_image_b64=reveal_image_b64,
            story_text=cover_description,
            character_emotion="excited",
            source_type=source_type,
            second_character_image_b64=second_character_image_b64,
            second_character_name=second_character_name,
            second_character_description=second_character_description,
        ))
        
        cover_with_text_b64 = create_front_cover(cover_image_b64, full_title, character_name)
        cover_url = upload_to_firebase(cover_with_text_b64, folder="adventure/storybooks")
        
        # Generate region map for cover page
        cover_mask_url = ""
        try:
            import base64
            from region_map import generate_region_map
            cover_bytes_for_mask = base64.b64decode(cover_with_text_b64)
            cover_region_bytes, cover_num_regions = generate_region_map(cover_bytes_for_mask)
            cover_mask_b64 = base64.b64encode(cover_region_bytes).decode("utf-8")
            cover_mask_url = upload_to_firebase(cover_mask_b64, folder="masks/storybooks")
            print(f"[WORKER] ✅ Cover region map ({cover_num_regions} regions)")
        except Exception as e:
            print(f"[WORKER] ⚠️ Cover region map failed (non-fatal): {e}")
        
        pages = [{"page_num": 0, "page_type": "cover", "title": full_title, "page_url": cover_url, "raw_image_url": cover_url, "mask_url": cover_mask_url, "story_text": ""}]
        
        # === STEP 3: Generate episode pages ===
        previous_page_b64 = None
        
        for i, episode in enumerate(episodes):
            update_job_status(job_id, "processing", progress=f"Drawing page {i+1} of {len(episodes)}...")
            
            scene_prompt = episode.get("scene_description", "").replace("{name}", character_name)
            story_text = episode.get("story_text", "").replace("{name}", character_name)
            episode_title = episode.get("title", f"Episode {i+1}")
            character_emotion = episode.get("character_emotion", "happy")
            parent_prompt = episode.get("parent_prompt")
            
            image_b64 = run_async(generate_adventure_episode_gemini(
                character_data={"name": character_name, "description": character_description, "key_feature": character_key_feature},
                scene_prompt=scene_prompt,
                age_rules=age_rules["rules"],
                reveal_image_b64=reveal_image_b64,
                story_text=story_text,
                character_emotion=character_emotion,
                source_type=source_type,
                previous_page_b64=previous_page_b64,
                second_character_image_b64=second_character_image_b64,
                second_character_name=second_character_name,
                second_character_description=second_character_description,
            ))
            
            # Validate for duplicate main characters — retry once if failed
            validation = run_async(validate_episode_image(image_b64))
            if not validation["pass"]:
                print(f"[WORKER] Episode {i+1} failed validation, regenerating...")
                image_b64 = run_async(generate_adventure_episode_gemini(
                    character_data={"name": character_name, "description": character_description, "key_feature": character_key_feature},
                    scene_prompt=scene_prompt,
                    age_rules=age_rules["rules"],
                    reveal_image_b64=reveal_image_b64,
                    story_text=story_text,
                    character_emotion=character_emotion,
                    source_type=source_type,
                    previous_page_b64=previous_page_b64,
                    second_character_image_b64=second_character_image_b64,
                    second_character_name=second_character_name,
                    second_character_description=second_character_description,
                ))
            
            previous_page_b64 = image_b64
            
            a4_page_b64 = create_a4_page_with_text(image_b64, story_text, episode_title, parent_prompt=parent_prompt)
            page_url = upload_to_firebase(a4_page_b64, folder="adventure/storybooks")
            raw_image_url = upload_to_firebase(image_b64, folder="adventure/storybooks/raw")
            
            # Generate region map for stay-in-the-lines colouring
            mask_url = ""
            try:
                import base64
                from region_map import generate_region_map
                image_bytes_for_mask = base64.b64decode(image_b64)
                region_map_bytes, num_regions = generate_region_map(image_bytes_for_mask)
                mask_b64 = base64.b64encode(region_map_bytes).decode("utf-8")
                mask_url = upload_to_firebase(mask_b64, folder="masks/storybooks")
                print(f"[WORKER] ✅ Story page {i+1} region map ({num_regions} regions)")
            except Exception as e:
                print(f"[WORKER] ⚠️ Story page {i+1} region map failed (non-fatal): {e}")
            
            pages.append({
                "page_num": i + 1,
                "page_type": "episode",
                "title": episode_title,
                "page_url": page_url,
                "raw_image_url": raw_image_url,
                "mask_url": mask_url,
                "story_text": story_text
            })
        
        # === STEP 4: Complete ===
        update_job_status(job_id, "complete", result={
            "pages": pages,
            "title": full_title,
            "total_pages": len(pages),
        })
        
        # Save storybook to Firestore with pages data for colour-on-device
        user_id = params.get("user_id", "")
        try:
            try:
                from google.cloud import firestore as gc_firestore
                db = gc_firestore.Client()
            except Exception:
                from firebase_admin import firestore as fb_firestore
                db = fb_firestore.client()
            from datetime import datetime
            # Read reveal URLs from user doc (saved by reveal flow task)
            user_doc = db.collection("users").document(user_id).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            saved_reveal_url = user_data.get("latest_reveal_url", "")
            saved_second_reveal_url = user_data.get("latest_second_reveal_url", "")
            storybook_doc = {
                "user_id": user_id,
                "title": full_title,
                "character_name": character_name,
                "age_level": age_level,
                "cover_url": cover_url,
                "reveal_url": saved_reveal_url,
                "second_reveal_url": saved_second_reveal_url,
                "reveal_url_string": saved_reveal_url,
                "second_reveal_url_string": saved_second_reveal_url,
                "total_pages": len(pages),
                "created_at": datetime.utcnow(),
                "pdf_url": "",
                "pages": pages,
            }
            _, storybook_ref = db.collection("storybooks").add(storybook_doc)
            print(f"[WORKER] Storybook saved to Firestore: {full_title} (id={storybook_ref.id})")
            
            # Save each page as a sub-collection document for FlutterFlow
            for page in pages:
                page_doc_id = f"page_{page['page_num']}"
                db.collection("storybooks").document(storybook_ref.id).collection("pages").document(page_doc_id).set({
                    "page_num": page["page_num"],
                    "page_type": page.get("page_type", "episode"),
                    "title": page.get("title", ""),
                    "page_url": page.get("page_url", ""),
                    "raw_image_url": page.get("raw_image_url", ""),
                    "mask_url": page.get("mask_url", ""),
                    "story_text": page.get("story_text", ""),
                })
            print(f"[WORKER] Saved {len(pages)} pages to sub-collection")
        except Exception as e:
            print(f"[WORKER] Firestore save failed (non-fatal): {e}")

        # Send push notification
        try:
            from push_notifications import send_push
            send_push(user_id, "Story Complete! 📖", f"{full_title} is ready to read!", {"type": "story", "job_id": job_id})
        except Exception as e:
            print(f"[WORKER] Push notification failed (non-fatal): {e}")
        
        print(f"[WORKER] ✅ Story complete: {full_title}")
        
    except Exception as e:
        print(f"[WORKER] ❌ Task failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.extract_and_reveal_task', bind=True, acks_late=True, reject_on_worker_lost=True)
def extract_and_reveal_task(self, job_id: str, params: dict):
    """Extract character from drawing/photo and generate Pixar reveal."""
    try:
        update_job_status(job_id, "processing", progress="Analysing your drawing...")
        
        # Force path fix inside task
        import sys, os
        task_dir = os.path.dirname(os.path.abspath(__file__))
        if task_dir not in sys.path:
            sys.path.insert(0, task_dir)
        
        from character_extraction_gemini import extract_character_with_extreme_accuracy
        from adventure_gemini import generate_adventure_reveal_gemini
        from firebase_utils import upload_to_firebase
        import base64
        
        image_b64 = params.get("image_b64")
        image_url = params.get("image_url")
        character_name = params.get("character_name", "Character")
        from app import normalize_age_level
        age_level = normalize_age_level(params.get("age_level", "age_5"))
        print(f"[REVEAL-TASK] raw: {params.get('age_level')}, normalized: {age_level}")
        
        # Download image from Firebase URL if b64 not provided
        if image_url and not image_b64:
            import httpx
            resp = httpx.get(image_url, timeout=30)
            image_bytes = resp.content
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            print(f"[WORKER] Downloaded image from URL, b64 length: {len(image_b64)}")
        else:
            image_bytes = base64.b64decode(image_b64)
        
        # Extract character
        update_job_status(job_id, "processing", progress="Understanding your character...")
        extraction_result = run_async(extract_character_with_extreme_accuracy(image_bytes, character_name))
        
        # Generate reveal
        update_job_status(job_id, "processing", progress="Bringing your character to life...")
        reveal_image_b64 = run_async(generate_adventure_reveal_gemini(
            character_data={
                'name': character_name,
                'description': extraction_result['reveal_description'],
                'key_feature': extraction_result['character']['key_feature'],
                'source_type': extraction_result.get('source_type', 'drawing')
            },
            original_drawing_b64=image_b64
        ))
        
        # Upload reveal to Firebase
        reveal_url = upload_to_firebase(reveal_image_b64, folder="adventure/reveals")
        
        update_job_status(job_id, "complete", result={
            "character": extraction_result["character"],
            "reveal_description": extraction_result["reveal_description"],
            "reveal_image_url": reveal_url,
            "reveal_image_b64": reveal_image_b64,
            "source_type": extraction_result.get("source_type", "drawing"),
        })
        
        # Save reveal URL to user doc so story task can access it
        try:
            try:
                from google.cloud import firestore as gc_firestore
                db_reveal = gc_firestore.Client()
            except Exception:
                from firebase_admin import firestore as fb_firestore
                db_reveal = fb_firestore.client()
            user_id = params.get("user_id", "")
            if user_id:
                is_second = params.get("is_second_character", False)
                if is_second:
                    db_reveal.collection("users").document(user_id).update({
                        "latest_second_reveal_url": reveal_url or "",
                    })
                else:
                    db_reveal.collection("users").document(user_id).update({
                        "latest_reveal_url": reveal_url or "",
                        "latest_second_reveal_url": "",
                    })
                print(f"[WORKER] Saved reveal URL to user doc: {user_id} (second={is_second})")
        except Exception as e:
            print(f"[WORKER] Failed to save reveal URL to user doc (non-fatal): {e}")

        # Send push notification
        try:
            from push_notifications import send_push
            send_push(user_id, "Character Revealed! ✨", f"Meet {character_name}!", {"type": "reveal", "job_id": job_id})
        except Exception as e:
            print(f"[WORKER] Push notification failed (non-fatal): {e}")
        
        print(f"[WORKER] ✅ Reveal complete: {character_name}")
        
    except Exception as e:
        print(f"[WORKER] ❌ Extract+reveal failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.character_reveal_flow_task', bind=True, acks_late=True, reject_on_worker_lost=True)
def character_reveal_flow_task(self, job_id: str, params: dict):
    """
    Full character reveal orchestrator:
    1. Extract + reveal first character
    2. (Optional) Extract + reveal second character  
    3. Generate 3 story pitches
    Returns everything needed for the CharacterReveal page.
    """
    try:
        import sys, os
        task_dir = os.path.dirname(os.path.abspath(__file__))
        if task_dir not in sys.path:
            sys.path.insert(0, task_dir)

        from character_extraction_gemini import extract_character_with_extreme_accuracy
        from adventure_gemini import generate_adventure_reveal_gemini
        from gemini_story_engine import generate_story_pitches_gemini
        from firebase_utils import upload_to_firebase
        from app import normalize_age_level
        import base64

        character_name = params.get("character_name", "Character")
        image_url = params.get("image_url")
        age_level = normalize_age_level(params.get("age_level", "age_5"))
        writing_style = params.get("writing_style")
        life_lesson = params.get("life_lesson")
        custom_theme = params.get("custom_theme")
        
        # Second character params (optional)
        has_second = params.get("has_second_character", False)
        second_character_name = params.get("second_character_name")
        second_image_url = params.get("second_image_url")

        # ========== STEP 1: First character extract + reveal ==========
        update_job_status(job_id, "processing", progress="Analysing your drawing...")
        
        # Download image from Firebase URL
        import httpx
        resp = httpx.get(image_url, timeout=30)
        image_bytes = resp.content
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        extraction_result = run_async(extract_character_with_extreme_accuracy(image_bytes, character_name))
        
        update_job_status(job_id, "processing", progress="Bringing your character to life...")
        
        reveal_image_b64 = run_async(generate_adventure_reveal_gemini(
            character_data={
                'name': character_name,
                'description': extraction_result['reveal_description'],
                'key_feature': extraction_result['character']['key_feature'],
                'source_type': extraction_result.get('source_type', 'drawing')
            },
            original_drawing_b64=image_b64
        ))
        
        reveal_url = upload_to_firebase(reveal_image_b64, folder="adventure/reveals")
        
        # ========== STEP 2: Second character (if provided) ==========
        second_result = None
        second_reveal_url = None
        second_reveal_b64 = None
        
        if has_second and second_image_url and second_character_name:
            update_job_status(job_id, "processing", progress=f"Analysing {second_character_name}...")
            
            # Download second image from Firebase URL
            resp2 = httpx.get(second_image_url, timeout=30)
            second_bytes = resp2.content
            second_image_b64 = base64.b64encode(second_bytes).decode('utf-8')
            second_extraction = run_async(extract_character_with_extreme_accuracy(second_bytes, second_character_name))
            
            update_job_status(job_id, "processing", progress=f"Bringing {second_character_name} to life...")
            
            second_reveal_b64 = run_async(generate_adventure_reveal_gemini(
                character_data={
                    'name': second_character_name,
                    'description': second_extraction['reveal_description'],
                    'key_feature': second_extraction['character']['key_feature'],
                    'source_type': second_extraction.get('source_type', 'drawing')
                },
                original_drawing_b64=second_image_b64
            ))
            
            second_reveal_url = upload_to_firebase(second_reveal_b64, folder="adventure/reveals")
            second_result = {
                "character": second_extraction["character"],
                "reveal_description": second_extraction["reveal_description"],
                "reveal_image_url": second_reveal_url,
                "source_type": second_extraction.get("source_type", "drawing"),
            }

        # ========== STEP 3: Generate story pitches ==========
        update_job_status(job_id, "processing", progress="Writing your stories...")
        
        stories_result = generate_story_pitches_gemini(
            character_name=character_name,
            character_description=extraction_result['reveal_description'],
            age_level=age_level,
            writing_style=writing_style,
            life_lesson=life_lesson,
            custom_theme=custom_theme,
            second_character_name=second_character_name if has_second else None,
            second_character_description=second_result["reveal_description"] if second_result else None
        )

        # ========== DONE ==========
        update_job_status(job_id, "complete", result={
            "character": extraction_result["character"],
            "character_name": character_name,
            "reveal_description": extraction_result["reveal_description"],
            "reveal_image_url": reveal_url,
            "reveal_image_b64": "",
            "source_type": extraction_result.get("source_type", "drawing"),
            "age_level": age_level,
            "writing_style": writing_style or "",
            "life_lesson": life_lesson or "",
            "custom_theme": custom_theme or "",
            "second_character": second_result or {},
            "second_character_name": second_character_name or "",
            "second_reveal_image_url": second_reveal_url or "",
            "second_reveal_image_b64": "",
            "second_image_b64": "",
            "stories": stories_result,
        })

        # Save reveal URLs to user doc so story task can access them
        try:
            try:
                from google.cloud import firestore as gc_firestore
                db_reveal = gc_firestore.Client()
            except Exception:
                from firebase_admin import firestore as fb_firestore
                db_reveal = fb_firestore.client()
            user_id = params.get("user_id", "")
            if user_id:
                db_reveal.collection("users").document(user_id).update({
                    "latest_reveal_url": reveal_url or "",
                    "latest_second_reveal_url": second_reveal_url or "",
                })
                print(f"[WORKER] Saved reveal URLs to user doc: {user_id}")
        except Exception as e:
            print(f"[WORKER] Failed to save reveal URLs to user doc (non-fatal): {e}")

        # Send push notification
        try:
            from push_notifications import send_push
            send_push(user_id, "Character Ready! ✨", f"Meet {character_name} and pick a story!", {"type": "reveal_flow", "job_id": job_id})
        except Exception as e:
            print(f"[WORKER] Push notification failed (non-fatal): {e}")

        print(f"[WORKER] ✅ Full reveal flow complete: {character_name}")

    except Exception as e:
        print(f"[WORKER] ❌ Reveal flow failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.generate_colouring_page_task', bind=True, acks_late=True, reject_on_worker_lost=True)
def generate_colouring_page_task(self, job_id: str, params: dict):
    """Generate a single colouring page (photo or text mode)."""
    try:
        update_job_status(job_id, "processing", progress="Creating your colouring page...")
        
        # Force path fix inside task
        import sys, os
        task_dir = os.path.dirname(os.path.abspath(__file__))
        if task_dir not in sys.path:
            sys.path.insert(0, task_dir)
        
        import base64
        import httpx
        from app import (
            build_photo_prompt, build_text_to_image_prompt,
            normalize_age_level, normalize_theme,
            is_valid_coloring_page, log_generation_attempt,
            OPENAI_API_KEY, BASE_URL, load_prompts, CONFIG
        )
        
        # Ensure CONFIG is loaded (Celery worker doesn't trigger FastAPI startup)
        import app as _app_module
        if _app_module.CONFIG is None:
            _app_module.CONFIG = load_prompts()
        from pdf_utils import create_a4_pdf
        from firebase_utils import upload_to_firebase
        from PIL import Image, ImageOps
        import io
        
        mode = params.get("mode", "text")  # "photo" or "text"
        age_level = normalize_age_level(params.get("age_level") or params.get("ageLevel", "age_5"))
        quality = params.get("quality", "low")
        
        if mode == "photo":
            # === PHOTO MODE ===
            image_b64 = params.get("image_b64") or params.get("imageB64", "")
            print(f"[WORKER] image_b64 length: {len(image_b64) if image_b64 else 0}")
            theme = normalize_theme(params.get("theme", "none"))
            custom_theme = params.get("custom_theme") or params.get("customTheme")
            if custom_theme in [None, "null", "", "None"]:
                custom_theme = None
            
            prompt = build_photo_prompt(age_level=age_level, theme=theme, custom_theme=custom_theme)
            
            update_job_status(job_id, "processing", progress="Generating your colouring page...")
            
            # Detect orientation
            image_bytes = base64.b64decode(image_b64)
            img = Image.open(io.BytesIO(image_bytes))
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            size = "1536x1024" if width > height else "1024x1536"
            
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            files = [("image[]", ("source.jpg", image_bytes, "image/jpeg"))]
            data = {
                "model": "gpt-image-1.5",
                "prompt": prompt,
                "n": "1",
                "size": size,
                "quality": quality,
            }
            
            with httpx.Client(timeout=180.0) as client:
                response = client.post(f"{BASE_URL}/images/edits", headers=headers, files=files, data=data)
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code} - {response.text[:200]}")
                result = response.json()
            
            image_data = result["data"][0]
            if "b64_json" in image_data:
                output_b64 = image_data["b64_json"]
            else:
                with httpx.Client() as client:
                    resp = client.get(image_data["url"])
                    output_b64 = base64.b64encode(resp.content).decode('utf-8')
            
            theme_used = custom_theme or theme
            
        elif mode == "pattern":
            # === PATTERN MODE ===
            from pattern_config import generate_pattern_prompt
            shape = params.get("description", "")
            prompt = generate_pattern_prompt(shape, age_level)
            
            update_job_status(job_id, "processing", progress="Generating your pattern...")
            
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            gen_data = {
                "model": "gpt-image-1.5",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1536",
                "quality": quality,
                "background": "opaque",
            }
            
            output_b64 = None
            for attempt in range(1, 4):
                with httpx.Client(timeout=180.0) as client:
                    response = client.post(f"{BASE_URL}/images/generations", headers=headers, json=gen_data)
                    if response.status_code != 200:
                        raise Exception(f"OpenAI API error: {response.status_code} - {response.text[:200]}")
                    result = response.json()
                
                image_data = result["data"][0]
                if "b64_json" in image_data:
                    output_b64 = image_data["b64_json"]
                else:
                    with httpx.Client() as client:
                        resp = client.get(image_data["url"])
                        output_b64 = base64.b64encode(resp.content).decode("utf-8")
                
                is_valid, brightness = is_valid_coloring_page(output_b64)
                log_generation_attempt(prompt[:100], attempt, is_valid, brightness, attempt > 1)
                
                if is_valid:
                    break
                elif attempt < 3:
                    update_job_status(job_id, "processing", progress=f"Retrying (attempt {attempt + 1})...")
            
            if not output_b64 or not is_valid:
                raise Exception("Failed to generate valid pattern after 3 attempts")
            
            theme_used = shape
            
        else:
            # === TEXT MODE ===
            description = params.get("description", "")
            prompt = build_text_to_image_prompt(description, age_level)
            
            update_job_status(job_id, "processing", progress="Generating your colouring page...")
            
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            gen_data = {
                "model": "gpt-image-1.5",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1536",
                "quality": quality,
                "background": "opaque",
            }
            
            # Try up to 3 times for dark image retry
            output_b64 = None
            for attempt in range(1, 4):
                with httpx.Client(timeout=180.0) as client:
                    response = client.post(f"{BASE_URL}/images/generations", headers=headers, json=gen_data)
                    if response.status_code != 200:
                        raise Exception(f"OpenAI API error: {response.status_code} - {response.text[:200]}")
                    result = response.json()
                
                image_data = result["data"][0]
                if "b64_json" in image_data:
                    output_b64 = image_data["b64_json"]
                else:
                    with httpx.Client() as client:
                        resp = client.get(image_data["url"])
                        output_b64 = base64.b64encode(resp.content).decode('utf-8')
                
                is_valid, brightness = is_valid_coloring_page(output_b64)
                log_generation_attempt(prompt[:100], attempt, is_valid, brightness, attempt > 1)
                
                if is_valid:
                    if attempt > 1:
                        print(f"[WORKER] Colouring page: attempt {attempt} success (brightness={brightness:.0f})")
                    break
                print(f"[WORKER] Colouring page: attempt {attempt} dark (brightness={brightness:.0f}), retrying...")
            
            theme_used = description
        
        # Upload image to Firebase
        update_job_status(job_id, "processing", progress="Saving your creation...")
        image_url = upload_to_firebase(output_b64, folder="generations")
        
        # Generate PDF
        pdf_url = None
        try:
            pdf_b64 = create_a4_pdf(output_b64)
            pdf_url = upload_to_firebase(pdf_b64, folder="pdfs")
        except Exception as e:
            print(f"[WORKER] PDF generation failed (non-fatal): {e}")
        
        # Detect orientation
        output_img = Image.open(io.BytesIO(base64.b64decode(output_b64)))
        is_landscape = output_img.width > output_img.height
        
        # Generate region map for colour-on-screen feature
        mask_url = None
        try:
            from region_map import generate_region_map
            image_bytes_for_mask = base64.b64decode(output_b64)
            region_map_bytes, num_regions = generate_region_map(image_bytes_for_mask)
            mask_b64 = base64.b64encode(region_map_bytes).decode("utf-8")
            mask_url = upload_to_firebase(mask_b64, folder="masks")
            print(f"[WORKER] ✅ Region map uploaded ({num_regions} regions): {mask_url}")
        except Exception as e:
            print(f"[WORKER] ⚠️ Region map generation failed (non-fatal): {e}")
        
        update_job_status(job_id, "complete", result={
            "image_url": image_url,
            "pdf_url": pdf_url,
            "mask_url": mask_url,
            "is_landscape": is_landscape,
            "theme_used": theme_used,
            "age_level": age_level,
        })
        
        # Send push notification
        try:
            from push_notifications import send_push
            user_id = params.get("user_id", "")
            send_push(user_id, "Colouring Page Ready! 🎨", "Your creation is waiting for you!", {"type": "colouring", "job_id": job_id})
        except Exception as e:
            print(f"[WORKER] Push notification failed (non-fatal): {e}")
        
        print(f"[WORKER] ✅ Colouring page complete: {theme_used}")
        
    except Exception as e:
        print(f"[WORKER] ❌ Colouring page failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.generate_storybook_pdf_task', bind=True, acks_late=True, reject_on_worker_lost=True)
def generate_storybook_pdf_task(self, job_id: str, params: dict):
    """Generate storybook PDF from completed pages."""
    try:
        update_job_status(job_id, "processing", progress="Building your storybook PDF...")
        
        # This will be filled in when we migrate the PDF endpoint
        # For now it's a placeholder
        update_job_status(job_id, "failed", error="PDF task not yet implemented")
        
    except Exception as e:
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.generate_pack_task', bind=True, time_limit=900, soft_time_limit=840, acks_late=True, reject_on_worker_lost=True)
def generate_pack_task(self, job_id: str, params: dict):
    """
    Generate an entire colouring page pack (8-12 pages) sequentially,
    stitch into a single PDF, upload to Firebase Storage.
    
    Uses the same OpenAI API call pattern as generate_colouring_page_task text mode.
    Extended time limits: 900s hard / 840s soft (vs 600/540 for single pages).
    
    params = {
        "pack_id": str,          # e.g. "farm_animals"
        "pack_name": str,        # e.g. "Farm Animals"
        "age_level": str,        # e.g. "age_4"
        "subjects": [str],       # e.g. ["a friendly cow standing in a meadow", ...]
        "user_id": str,
        "quality": str,          # "low" or "high", default "low"
    }
    """
    try:
        update_job_status(job_id, "processing", progress="Starting pack generation...")

        # Force path fix inside task (same pattern as all other tasks)
        import sys, os
        task_dir = os.path.dirname(os.path.abspath(__file__))
        if task_dir not in sys.path:
            sys.path.insert(0, task_dir)

        import base64
        import io
        import httpx
        from datetime import datetime
        from PIL import Image
        from pypdf import PdfWriter, PdfReader
        from app import (
            build_text_to_image_prompt, normalize_age_level,
            is_valid_coloring_page, log_generation_attempt,
            OPENAI_API_KEY, BASE_URL, load_prompts, CONFIG
        )
        from firebase_utils import upload_to_firebase

        # Ensure CONFIG is loaded (Celery worker doesn't trigger FastAPI startup)
        import app as _app_module
        if _app_module.CONFIG is None:
            _app_module.CONFIG = load_prompts()

        subjects = params.get("subjects", [])
        total = len(subjects)
        pack_id = params.get("pack_id", "unknown")
        pack_name = params.get("pack_name", "Colouring Pack")
        age_level = normalize_age_level(params.get("age_level", "age_5"))
        quality = params.get("quality", "low")
        user_id = params.get("user_id", "")

        generated_images = []  # list of (subject, PIL.Image) tuples
        generated_pages = []   # list of dicts with individual page URLs
        failed_subjects = []

        for i, subject in enumerate(subjects):
            page_num = i + 1
            update_job_status(
                job_id, "processing",
                progress=f"Drawing page {page_num} of {total}...",
                result={
                    "pack_progress": {
                        "completed": i,
                        "total": total,
                        "current_subject": subject,
                        "pack_name": pack_name,
                    }
                }
            )

            try:
                # Build prompt — same function as single colouring page text mode
                prompt = build_text_to_image_prompt(subject, age_level)

                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                gen_data = {
                    "model": "gpt-image-1.5",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1536",
                    "quality": quality,
                    "background": "opaque",
                }

                # Try up to 3 times for dark image retry (same as single page)
                output_b64 = None
                for attempt in range(1, 4):
                    with httpx.Client(timeout=180.0) as client:
                        response = client.post(
                            f"{BASE_URL}/images/generations",
                            headers=headers, json=gen_data
                        )
                        if response.status_code != 200:
                            raise Exception(
                                f"OpenAI API error: {response.status_code} - {response.text[:200]}"
                            )
                        result = response.json()

                    image_data = result["data"][0]
                    if "b64_json" in image_data:
                        output_b64 = image_data["b64_json"]
                    else:
                        with httpx.Client() as dl_client:
                            resp = dl_client.get(image_data["url"])
                            output_b64 = base64.b64encode(resp.content).decode('utf-8')

                    is_valid, brightness = is_valid_coloring_page(output_b64)
                    log_generation_attempt(
                        f"[PACK:{pack_id}] {prompt[:80]}",
                        attempt, is_valid, brightness, attempt > 1
                    )

                    if is_valid:
                        if attempt > 1:
                            print(f"[WORKER-PACK] Page {page_num}/{total} '{subject[:40]}': "
                                  f"attempt {attempt} success (brightness={brightness:.0f})")
                        break
                    print(f"[WORKER-PACK] Page {page_num}/{total} '{subject[:40]}': "
                          f"attempt {attempt} dark (brightness={brightness:.0f}), retrying...")

                if output_b64 is None:
                    raise Exception("All attempts produced dark images")

                # Upload individual image
                image_url = upload_to_firebase(output_b64, folder="generations")

                # Generate individual PDF
                individual_pdf_url = None
                try:
                    from pdf_utils import create_a4_pdf
                    ind_pdf_b64 = create_a4_pdf(output_b64)
                    individual_pdf_url = upload_to_firebase(ind_pdf_b64, folder="pdfs")
                except Exception as pdf_err:
                    print(f"[WORKER-PACK] ⚠️ Individual PDF failed (non-fatal): {pdf_err}")

                # Generate region mask for colour-on-screen
                mask_url = None
                try:
                    from region_map import generate_region_map
                    image_bytes_for_mask = base64.b64decode(output_b64)
                    region_map_bytes, num_regions = generate_region_map(image_bytes_for_mask)
                    mask_b64 = base64.b64encode(region_map_bytes).decode("utf-8")
                    mask_url = upload_to_firebase(mask_b64, folder="masks")
                except Exception as mask_err:
                    print(f"[WORKER-PACK] ⚠️ Region map failed (non-fatal): {mask_err}")

                # Detect orientation
                img = Image.open(io.BytesIO(base64.b64decode(output_b64)))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                is_landscape = img.width > img.height

                generated_images.append((subject, img))
                generated_pages.append({
                    "image_url": image_url,
                    "pdf_url": individual_pdf_url,
                    "mask_url": mask_url,
                    "is_landscape": is_landscape,
                    "theme_used": subject,
                    "age_level": age_level,
                })

                print(f"[WORKER-PACK] ✅ Page {page_num}/{total} done: {subject[:50]}")

            except Exception as page_err:
                print(f"[WORKER-PACK] ⚠️ Page {page_num}/{total} failed: {subject[:50]} — {page_err}")
                failed_subjects.append(subject)
                continue

        if not generated_images:
            update_job_status(job_id, "failed", error="No pages were generated successfully")
            return

        # --- Stitch all pages into a single PDF ---
        update_job_status(
            job_id, "processing",
            progress=f"Stitching {len(generated_images)} pages into PDF...",
            result={
                "pack_progress": {
                    "completed": len(generated_images),
                    "total": total,
                    "current_subject": None,
                    "pack_name": pack_name,
                }
            }
        )

        # A4 at 150 DPI = 1240 x 1754 px
        TARGET_W, TARGET_H = 1240, 1754
        pdf_writer = PdfWriter()

        for subject, img in generated_images:
            img_ratio = img.width / img.height
            target_ratio = TARGET_W / TARGET_H

            if img_ratio > target_ratio:
                new_w = TARGET_W
                new_h = int(TARGET_W / img_ratio)
            else:
                new_h = TARGET_H
                new_w = int(TARGET_H * img_ratio)

            img_resized = img.resize((new_w, new_h), Image.LANCZOS)

            canvas = Image.new("RGB", (TARGET_W, TARGET_H), "white")
            x_offset = (TARGET_W - new_w) // 2
            y_offset = (TARGET_H - new_h) // 2
            canvas.paste(img_resized, (x_offset, y_offset))

            page_pdf_bytes = io.BytesIO()
            canvas.save(page_pdf_bytes, format="PDF", resolution=150)
            page_pdf_bytes.seek(0)

            page_reader = PdfReader(page_pdf_bytes)
            pdf_writer.add_page(page_reader.pages[0])

        combined_pdf_bytes = io.BytesIO()
        pdf_writer.write(combined_pdf_bytes)
        combined_pdf_bytes.seek(0)

        # --- Save individual pages to Firestore ---
        try:
            from google.cloud import firestore as gc_firestore
            db = gc_firestore.Client()
        except Exception:
            import firebase_admin
            from firebase_admin import firestore as fb_firestore
            db = fb_firestore.client()

        for page_data in generated_pages:
            try:
                db.collection("colouring_pages").add({
                    "user_id": user_id,
                    "image_url": page_data["image_url"],
                    "pdf_url": page_data.get("pdf_url"),
                    "mask_url": page_data.get("mask_url"),
                    "theme": page_data["theme_used"],
                    "age_level": page_data["age_level"],
                    "is_landscape": page_data.get("is_landscape", False),
                    "created_at": datetime.utcnow(),
                    "pack_id": pack_id,
                    "pack_name": pack_name,
                })
            except Exception as fs_err:
                print(f"[WORKER-PACK] ⚠️ Firestore save failed for {page_data['theme_used']}: {fs_err}")

        print(f"[WORKER-PACK] ✅ Saved {len(generated_pages)} pages to Firestore")

        # --- Upload combined PDF to Firebase Storage ---
        pdf_b64 = base64.b64encode(combined_pdf_bytes.read()).decode('utf-8')
        pdf_url = upload_to_firebase(pdf_b64, folder="packs", content_type="application/pdf")

        print(f"[WORKER-PACK] ✅ Pack PDF uploaded: {pdf_url}")

        # --- Complete ---
        result_data = {
            "pdf_url": pdf_url,
            "pack_name": pack_name,
            "pack_id": pack_id,
            "age_level": age_level,
            "pages": generated_pages,
            "pages_generated": len(generated_images),
            "pages_failed": len(failed_subjects),
            "total_requested": total,
            "failed_subjects": failed_subjects,
            "pack_progress": {
                "completed": len(generated_images),
                "total": total,
                "current_subject": None,
                "pack_name": pack_name,
            }
        }

        update_job_status(job_id, "complete", result=result_data)

        # Send push notification
        try:
            from push_notifications import send_push
            send_push(
                user_id,
                f"{pack_name} Pack Ready! 🎨",
                f"Your {len(generated_images)}-page colouring pack is ready to download!",
                {"type": "pack", "job_id": job_id}
            )
        except Exception as e:
            print(f"[WORKER-PACK] Push notification failed (non-fatal): {e}")

        print(f"[WORKER-PACK] ✅ Pack complete: {pack_name} — "
              f"{len(generated_images)}/{total} pages, {len(failed_subjects)} failed")

    except Exception as e:
        print(f"[WORKER-PACK] ❌ Pack failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])
