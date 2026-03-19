"""
Little Lines — Celery Tasks
Heavy AI generation work that runs on workers, not the API server.
"""
import os
import json
import asyncio
import traceback
from celery_app import celery_app
from job_endpoints import update_job_status


def run_async(coro):
    """Helper to run async functions from sync Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name='tasks.generate_full_story_task', bind=True)
def generate_full_story_task(self, job_id: str, params: dict):
    """
    Generate a complete storybook: story text + cover + 5 episode images + PDF.
    This is the heaviest operation (~3-5 minutes).
    """
    try:
        update_job_status(job_id, "processing", progress="Starting story generation...")
        
        # Import here to avoid circular imports and ensure env vars are loaded
        from adventure_gemini import (
            generate_story_for_theme,
            generate_adventure_episode_gemini,
            create_a4_page_with_text,
            create_front_cover,
            validate_episode_image
        )
        from adventure_config import get_age_rules
        from firebase_utils import upload_to_firebase
        from adventure_config import ADVENTURE_THEMES
        
        # Extract params
        character_name = params.get("character_name", "Character")
        character_description = params.get("character_description", "")
        character_key_feature = params.get("character_key_feature", "")
        theme_name = params.get("theme_name", "")
        theme_description = params.get("theme_description", "")
        theme_blurb = params.get("theme_blurb", "")
        feature_used = params.get("feature_used", "")
        want = params.get("want", "")
        obstacle = params.get("obstacle", "")
        twist = params.get("twist", "")
        age_level = params.get("age_level", "age_5")
        writing_style = params.get("writing_style")
        life_lesson = params.get("life_lesson")
        custom_theme = params.get("custom_theme")
        reveal_image_b64 = params.get("reveal_image_b64")
        source_type = params.get("source_type", "drawing")
        second_character_name = params.get("second_character_name")
        second_character_description = params.get("second_character_description")
        second_character_image_b64 = params.get("second_character_image_b64")
        
        # Get age rules
        age_rules = get_age_rules(age_level)
        
        # === STEP 1: Generate story text with Sonnet ===
        update_job_status(job_id, "processing", progress="Writing your story...")
        
        story_data = run_async(generate_story_for_theme(
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
        ))
        
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
        
        pages = [{"page_num": 0, "page_type": "cover", "title": full_title, "page_url": cover_url, "story_text": ""}]
        
        # === STEP 3: Generate episode pages ===
        previous_page_b64 = None
        
        for i, episode in enumerate(episodes):
            update_job_status(job_id, "processing", progress=f"Drawing page {i+1} of {len(episodes)}...")
            
            scene_prompt = episode.get("scene_description", "").replace("{name}", character_name)
            story_text = episode.get("story_text", "").replace("{name}", character_name)
            episode_title = episode.get("title", f"Episode {i+1}")
            character_emotion = episode.get("character_emotion", "happy")
            
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
            
            a4_page_b64 = create_a4_page_with_text(image_b64, story_text, episode_title)
            page_url = upload_to_firebase(a4_page_b64, folder="adventure/storybooks")
            pages.append({
                "page_num": i + 1,
                "page_type": "episode",
                "title": episode_title,
                "page_url": page_url,
                "story_text": story_text
            })
        
        # === STEP 4: Complete ===
        update_job_status(job_id, "complete", result={
            "pages": pages,
            "title": full_title,
            "total_pages": len(pages),
        })
        
        print(f"[WORKER] ✅ Story complete: {full_title}")
        
    except Exception as e:
        print(f"[WORKER] ❌ Task failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.extract_and_reveal_task', bind=True)
def extract_and_reveal_task(self, job_id: str, params: dict):
    """Extract character from drawing/photo and generate Pixar reveal."""
    try:
        update_job_status(job_id, "processing", progress="Analysing your drawing...")
        
        from character_extraction_gemini import extract_character_with_extreme_accuracy
        from adventure_gemini import generate_adventure_reveal_gemini
        from firebase_utils import upload_to_firebase
        import base64
        
        image_b64 = params.get("image_b64")
        character_name = params.get("character_name", "Character")
        age_level = params.get("age_level", "age_5")
        
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
        
        print(f"[WORKER] ✅ Reveal complete: {character_name}")
        
    except Exception as e:
        print(f"[WORKER] ❌ Extract+reveal failed: {str(e)}")
        traceback.print_exc()
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.generate_colouring_page_task', bind=True)
def generate_colouring_page_task(self, job_id: str, params: dict):
    """Generate a single colouring page."""
    try:
        update_job_status(job_id, "processing", progress="Creating your colouring page...")
        
        # This will be filled in when we migrate the colouring page endpoint
        # For now it's a placeholder
        update_job_status(job_id, "failed", error="Colouring page task not yet implemented")
        
    except Exception as e:
        update_job_status(job_id, "failed", error=str(e)[:500])


@celery_app.task(name='tasks.generate_storybook_pdf_task', bind=True)
def generate_storybook_pdf_task(self, job_id: str, params: dict):
    """Generate storybook PDF from completed pages."""
    try:
        update_job_status(job_id, "processing", progress="Building your storybook PDF...")
        
        # This will be filled in when we migrate the PDF endpoint
        # For now it's a placeholder
        update_job_status(job_id, "failed", error="PDF task not yet implemented")
        
    except Exception as e:
        update_job_status(job_id, "failed", error=str(e)[:500])
