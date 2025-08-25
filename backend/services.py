# backend\services.py
import uuid
import json
from typing import Dict, Any, List
from .logger_config import logger
from fastapi import BackgroundTasks
from sqlmodel import Session, select
from .models import Job, engine, create_db_and_tables
from .storage import ensure_job_dir, save_json, save_image, get_job_files, read_json
from .providers import provider
from .utils import is_valid_url, truncate_text
from .logger_config import logger, log_call
from .prompts import (
    create_summary_messages, 
    create_post_variants_messages, 
    create_image_prompt_messages,
    create_moderation_messages
)
from datetime import datetime
import re
import ast

def _coerce_response_to_str(resp) -> str:
    """Coerce various response shapes (str, list, dict, objects) to a single string."""
    logger.info("Coercing response to string")
    if isinstance(resp, str):
        return resp
    if isinstance(resp, list):
        parts = []
        for el in resp:
            if isinstance(el, str):
                parts.append(el)
            elif isinstance(el, dict):
                try:
                    parts.append(json.dumps(el, ensure_ascii=False))
                except Exception:
                    parts.append(str(el))
            else:
                parts.append(str(el))
        return "\n".join(parts)
    if isinstance(resp, dict):
        try:
            return json.dumps(resp, ensure_ascii=False)
        except Exception:
            return str(resp)
    # Fallback: try to get 'content' attr
    content = getattr(resp, 'content', None)
    if isinstance(content, (str, list, dict)):
        return _coerce_response_to_str(content)
    return str(resp)


def _extract_json_from_text(text: str):
    logger.info("Extracting JSON from text")
    """Attempt to extract a JSON object/array from text and parse it.
    Tries heuristics: remove code fences, find {...} or [...], ast.literal_eval, and single-quote -> double-quote fallback.
    """
    if not text:
        raise ValueError("Empty text")

    # Remove leading/trailing code fences
    text = re.sub(r"\A```[a-zA-Z]*\n", "", text)
    text = text.rstrip('`\n')

    # Try to find first JSON-like substring
    m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
    candidate = m.group(1) if m else text.strip()

    # Try standard JSON
    try:
        return json.loads(candidate)
    except Exception:
        pass

    # Try ast.literal_eval (handles Python single quotes dicts/lists)
    try:
        return ast.literal_eval(candidate)
    except Exception:
        pass

    # As last resort, try converting single quotes to double quotes
    try:
        return json.loads(candidate.replace("'", '"'))
    except Exception as e:
        raise ValueError(f"Failed to parse model JSON response: {e}\nRaw: {candidate[:200]}")



async def create_job(url: str, opinion: str, tone: str, image_options: Dict[str, Any]) -> str:
    """Create a new job and return job_id."""
    logger.info("Creating new job")
    # Validate URL
    if not is_valid_url(url):
        raise ValueError("Invalid URL provided")

    # Reachability check: try HEAD then GET with retries
    try:
        import httpx
        import time

        last_exc = None
        for attempt in range(3):
            try:
                with httpx.Client(follow_redirects=True, timeout=10.0) as client:
                    # Prefer HEAD to be lightweight
                    try:
                        resp = client.head(url)
                    except Exception:
                        resp = client.get(url)

                    status = getattr(resp, 'status_code', None)
                    if status is not None and status < 400:
                        break
                    # if status indicates error, try GET once
                    if status is not None and status >= 400:
                        try:
                            resp = client.get(url)
                            status = getattr(resp, 'status_code', None)
                            if status is not None and status < 400:
                                break
                        except Exception as e:
                            last_exc = e
                            # fallthrough to retry
                    last_exc = None
            except Exception as e:
                last_exc = e
            # backoff
            time.sleep(1 + attempt)
        else:
            # All attempts failed
            msg = f"URL reachability check failed for {url}: {last_exc or 'no response'}"
            logger.warning(msg)
            raise ValueError(msg)
    except ImportError:
        # httpx not available — fall back to syntactic validation but warn
        logger.warning("httpx not available; skipping reachability check")
    except ValueError:
        # re-raise ValueError
        raise
    except Exception as e:
        logger.warning(f"Unexpected error during reachability check: {e}")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Create job directory
    job_dir = ensure_job_dir(job_id)

    # Persist metadata about the job to tmp/{job_id}/metadata.json
    try:
        metadata = {
            "job_id": job_id,
            "url": url,
            "opinion": opinion,
            "tone": tone,
            "image_options": image_options,
            "created_at": str(datetime.utcnow())
        }
        metadata_path = job_dir / "metadata.json"
        await save_json(metadata, metadata_path)
    except Exception:
        logger.exception("Failed to persist job metadata")

    # Create job record in database
    job = Job(
        job_id=job_id,
        url=url,
        opinion=opinion,
        tone=tone,
        image_options=json.dumps(image_options)
    )

    with Session(engine) as session:
        session.add(job)
        session.commit()
        session.refresh(job)

    logger.info(f"Created job {job_id} for URL: {url}")
    return job_id

async def run_job(job_id: str) -> None:
    """Run the complete job pipeline."""
    logger.info(f"Running job pipeline for job_id: {job_id}")
    try:
        with Session(engine) as session:
            # Get job record
            job = session.exec(select(Job).where(Job.job_id == job_id)).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Capture all required fields BEFORE the session closes to avoid detached instance access
            job_url = job.url
            job_opinion = job.opinion
            job_tone = job.tone
            job_image_options = job.get_image_options()
            # Update status to in_progress
            job.status = "in_progress"
            session.commit()
        
        # Run pipeline steps
        logger.info(f"Starting job pipeline for {job_id}")
        
        # Step 1: Scrape the URL
        scrape_data = await scrape_url(job_url)
        scrape_path = get_job_files(job_id)["scrape"]
        await save_json(scrape_data, scrape_path)
        
        # Step 2: Generate summary using LangChain
        summary_data = await generate_summary_with_langchain(scrape_data["main_text"])
        summary_path = get_job_files(job_id)["summary"]
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_data.get("summary", "Summary generation failed"))
        
        # Step 3: Generate post variants using LangChain
        variants = await generate_post_variants_with_langchain(
            summary_data.get("summary", ""),
            summary_data.get("bullets", []),
            job_opinion,
            job_tone,
            job_id
        )
        
        # Step 4: Generate images
        images = await generate_images_with_langchain(variants, job_image_options, job_id)
        
        # Step 5: Moderate content
        moderation_results = await moderate_content(variants)
        
        # Step 6: Save final result
        result = {
            "job_id": job_id,
            "provenance": {
                "source_url": job_url,
                "title": scrape_data.get("title", ""),
                "excerpt": truncate_text(scrape_data.get("main_text", ""), 200)
            },
            "post_variants": variants,
            "providers": {
                "text": provider.__class__.__name__,
                "image": provider.__class__.__name__
            },
            "moderation": moderation_results
        }
        
        result_path = get_job_files(job_id)["result"]
        await save_json(result, result_path)
        
        # Verify images exist for each variant; attempt one retry for missing images
        try:
            from pathlib import Path
            images_dir = Path(f"./tmp/{job_id}/images")
            missing = []
            
            for v in result["post_variants"]:
                # Use the actual file system path, not the API URL
                img_path = images_dir / f"{v.get('id')}.png"
                if not img_path.exists():
                    missing.append((v.get('id'), img_path))
            
            if missing:
                logger.warning(f"Missing images for job={job_id}: {missing}. Attempting one retry generation.")
                
                # Try to regenerate missing images once
                for variant_id, img_path in missing:
                    try:
                        # Find the variant record
                        variant = next((x for x in result["post_variants"] if x["id"] == variant_id), None)
                        if not variant:
                            continue
                            
                        # Generate image prompt
                        messages = create_image_prompt_messages(
                            variant['text'][:100],
                            job_image_options.get('style', 'photographic'),
                            job_image_options.get('negative_prompt', 'no text, no logos')
                        )
                        
                        image_prompt = await provider.generate_text(
                            prompt=str(messages[-1].content),
                            max_tokens=200,
                            temperature=0.5
                        )
                        
                        image_data = await provider.generate_image(
                            prompt=image_prompt,
                            negative_prompt=job_image_options.get('negative_prompt', 'no text, no logos'),
                            size=job_image_options.get('aspect_ratio', '16:9'),
                            job_id=job_id
                        )
                        
                        # Ensure directory exists
                        img_path.parent.mkdir(parents=True, exist_ok=True)
                        await save_image(image_data, img_path)
                        
                        # Update result path string with API URL
                        variant['image_path'] = f"/api/v1/images/{job_id}/{variant_id}.png"
                        logger.info(f"Regenerated missing image for job={job_id} variant={variant_id}")
                    except Exception as e:
                        logger.exception(f"Retry generation failed for job={job_id} variant={variant_id}: {e}")
                
                # Re-save result after attempts
                await save_json(result, result_path)
                
                # Re-check missing
                still_missing = []
                for v in result["post_variants"]:
                    img_path = images_dir / f"{v.get('id')}.png"
                    if not img_path.exists():
                        still_missing.append((v.get('id'), img_path))
                
                if still_missing:
                    err_msg = f"Images missing after retry for job={job_id}: {still_missing}"
                    logger.error(err_msg)
                    with Session(engine) as session:
                        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
                        if job:
                            job.status = "failed"
                            job.error = err_msg
                            session.commit()
                    return
        except Exception:
            logger.exception("Error during image verification/generation step")
        
        # Update job status to completed
        with Session(engine) as session:
            job = session.exec(select(Job).where(Job.job_id == job_id)).first()
            if job:
                job.status = "completed"
                job.result_path = str(result_path)
                session.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        # Update job status to failed
        with Session(engine) as session:
            job = session.exec(select(Job).where(Job.job_id == job_id)).first())
            if job:
                job.status = "failed"
                job.error = str(e)
                session.commit()

async def scrape_url(url: str) -> Dict[str, Any]:
    """Scrape content from URL."""
    logger.info(f"Scraping URL: {url}")
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Extract main content (simplified - in production, use more sophisticated extraction)
        main_content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text and len(text) > 20:  # Filter out very short text
                main_content.append(text)
        
        main_text = " ".join(main_content)
        
        # Extract bullets (look for list items)
        bullets = []
        for ul in soup.find_all(['ul', 'ol']):
            find_all_fn = getattr(ul, 'find_all', None)
            if not callable(find_all_fn):
                continue
            items = find_all_fn('li') or []
            # Ensure items is iterable (BeautifulSoup may return a PageElement or list)
            try:
                iter(items)
            except TypeError:
                items = [items]

            for li in items:
                try:
                    bullet_text = li.get_text().strip()
                except Exception:
                    bullet_text = str(li).strip()
                if bullet_text and len(bullet_text) > 10:
                    bullets.append(bullet_text)

        return {
            "url": url,
            "title": title_text,
            "main_text": main_text,
            "bullets": bullets[:5],  # Limit to 5 bullets
            "scraped_at": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {e}")
        raise Exception(f"Failed to scrape URL: {e}")



async def generate_summary_with_langchain(main_text: str) -> Dict[str, Any]:
    """Generate a summary using LangChain prompts."""
    logger.info("Generating summary with LangChain")
    try:
        # Create messages using LangChain
        messages = create_summary_messages(main_text[:2000])  # Limit text length

        # Get response from provider
        raw_response = await provider.generate_text(
            prompt=str(messages[-1].content),  # Use the human message content
            max_tokens=300,
            temperature=0.3
        )

        resp_text = _coerce_response_to_str(raw_response)

        # Try to parse JSON response
        try:
            parsed = _extract_json_from_text(resp_text)
            if isinstance(parsed, dict) and 'summary' in parsed:
                return parsed
            # Fallback: use raw text if structure unexpected
            return {
                "summary": resp_text,
                "bullets": ["Key point 1", "Key point 2", "Key point 3"]
            }
        except Exception:
            # Fallback: create basic summary
            return {
                "summary": resp_text,
                "bullets": ["Key point 1", "Key point 2", "Key point 3"]
            }

    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return {
            "summary": "Summary generation failed. Please try again.",
            "bullets": ["Error occurred during generation"]
        }

async def generate_post_variants_with_langchain(summary: str, bullets: List[str], opinion: str, tone: str, job_id: str) -> List[Dict[str, Any]]:
    """Generate two post variants using LangChain prompts."""
    logger.info("Generating post variants with LangChain")
    response_text = None
    try:
        # Create messages using LangChain
        messages = create_post_variants_messages(summary, bullets, opinion, tone)

        # Get response from provider
        raw_response = await provider.generate_text(
            prompt=str(messages[-1].content),
            max_tokens=800,
            temperature=0.7
        )

        response_text = _coerce_response_to_str(raw_response).strip()

        # If provider returned empty text, persist raw response for debugging and fallback
        if not response_text:
            try:
                logger.warning(f"Variants provider returned empty response for job={job_id}. Persisting raw response for debugging.")
                # Persist raw response representation to tmp debug folder
                if job_id:
                    from pathlib import Path
                    import time
                    debug_dir = Path(f"./tmp/{job_id}/debug")
                    debug_dir.mkdir(parents=True, exist_ok=True)
                    dump_path = debug_dir / f"variants_response_{int(time.time())}.txt"
                    with dump_path.open('w', encoding='utf-8') as fh:
                        fh.write(repr(raw_response))
            except Exception:
                logger.exception("Failed to persist empty variants raw response")

            return create_fallback_variants(summary, opinion, tone, job_id)

        # Log a safe preview of the raw response for debugging
        try:
            logger.debug(f"Variants raw response preview (first 10 chars): {response_text[:10]!r}")
        except Exception:
            logger.debug("Variants raw response preview unavailable")

        try:
            parsed = _extract_json_from_text(response_text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed response is not a dict")

            variants = []
            for variant_id in ["A", "B"]:
                if variant_id in parsed and isinstance(parsed[variant_id], dict):
                    variant_data = parsed[variant_id]
                    variants.append({
                        "id": variant_id,
                        "text": variant_data.get("text", ""),
                        "hashtags": variant_data.get("hashtags", []),
                        "suggested_comment": variant_data.get("suggested_comment", ""),
                        "alt_text": variant_data.get("alt_text", ""),
                        "image_path": f"/api/v1/images/{job_id}/{variant_id}.png"
                    })

            if len(variants) == 2:
                return variants
            else:
                raise ValueError("Incomplete variants generated")

        except Exception as e:
            # Include raw preview in the warning so we can see the exact model output
            try:
                logger.warning(f"Failed to parse variants response: {e}. Raw response preview: {response_text[:10]!r}")
            except Exception:
                logger.warning(f"Failed to parse variants response: {e}.")
            logger.exception("Variant parsing exception")
            return create_fallback_variants(summary, opinion, tone, job_id)

    except Exception as e:
        # Provide more context in logs for debugging
        try:
            if response_text:
                logger.error(f"Post variant generation failed: {e}. Raw response preview: {response_text[:10]!r}")
            else:
                logger.error(f"Post variant generation failed: {e}. No raw response available")
        except Exception:
            logger.error(f"Post variant generation failed: {e}")
        logger.exception("Post variant generation exception")
        return create_fallback_variants(summary, opinion, tone, job_id)

async def generate_images_with_langchain(variants: List[Dict[str, Any]], image_options: Dict[str, Any], job_id: str) -> bool:
    """Generate images for post variants using LangChain prompts."""
    logger.info(f"Generating images for job_id: {job_id} with options: {image_options}")
    try:
        job_files = get_job_files(job_id)
        images_paths = job_files.get("images", {}) if job_files else {}

        for variant in variants:
            variant_id = variant.get('id')
            # Determine target path from storage helper (Path)
            target_path = None
            if images_paths and variant_id in images_paths:
                target_path = images_paths[variant_id]
            else:
                # fallback
                from pathlib import Path
                target_path = Path(f"./tmp/{job_id}/images/{variant_id}.png")
                target_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate image prompt using LangChain
            messages = create_image_prompt_messages(
                variant['text'][:100],  # Limit text length
                image_options.get('style', 'photographic'),
                image_options.get('negative_prompt', 'no text, no logos')
            )

            image_prompt = await provider.generate_text(
                prompt=str(messages[-1].content),
                max_tokens=200,
                temperature=0.5
            )

            # Generate image (wrapped for better debug visibility)
            try:
                logger.debug(f"Generating image for job={job_id} variant={variant_id} using provider={provider.__class__.__name__} prompt={image_prompt}")
                image_data = await provider.generate_image(
                    prompt=image_prompt,
                    negative_prompt=image_options.get('negative_prompt', 'no text, no logos'),
                    size=image_options.get('aspect_ratio', '16:9'),
                    job_id=job_id
                )
            except Exception as e:
                # Log contextual information to help backtrack the failure
                logger.exception(f"Image generation failed for job={job_id} variant={variant_id} provider={provider.__class__.__name__} prompt={image_prompt} options={image_options}: {e}")
                # Try to use provider.generate_image as a fallback (provider may return placeholder)
                try:
                    image_data = await provider.generate_image(
                        prompt=image_prompt,
                        negative_prompt=image_options.get('negative_prompt', ''),
                        size=image_options.get('aspect_ratio', '16:9'),
                        job_id=job_id
                    )
                    logger.info(f"Using provider fallback image for job={job_id} variant={variant_id}")
                except Exception:
                    logger.exception("Failed to generate fallback image")
                    raise

            # Save image using storage helper path (Path object)
            try:
                await save_image(image_data, target_path)
            except Exception as e:
                logger.exception(f"Failed to save image for job={job_id} variant={variant_id} to {target_path}: {e}")
                return False

            # Update variant with correct image path (API URL for serialization)
            variant['image_path'] = f"/api/v1/images/{job_id}/{variant_id}.png"

        return True

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return False

async def moderate_content(variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Moderate generated content using LangChain."""
    logger.info("Starting content moderation")
    try:
        moderation_results = []
        
        for variant in variants:
            messages = create_moderation_messages(
                variant['text'],
                variant['hashtags'],
                variant['suggested_comment']
            )
            
            moderation_response = await provider.generate_text(
                prompt=str(messages[-1].content),
                max_tokens=200,
                temperature=0.1
            )
            
            logger.debug(f"Received moderation response: {moderation_response[:100] if moderation_response else 'EMPTY'}")
            
            # Check if response is empty
            if not moderation_response or not moderation_response.strip():
                logger.warning("Received empty response for moderation, using default")
                moderation_results.append({
                    "variant_id": variant['id'],
                    "status": "review",
                    "notes": ["Moderation service unavailable"],
                    "confidence": "low"
                })
                continue
            
            try:
                # Clean the response - remove any non-JSON formatting
                moderation_response = moderation_response.strip()
                if moderation_response.startswith('```json'):
                    moderation_response = moderation_response[7:]
                if moderation_response.endswith('```'):
                    moderation_response = moderation_response[:-3]
                
                parsed = json.loads(moderation_response)
                moderation_results.append({
                    "variant_id": variant['id'],
                    "status": parsed.get("status", "review"),
                    "notes": parsed.get("notes", []),
                    "confidence": parsed.get("confidence", "medium")
                })
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse moderation response: {e}, using default")
                moderation_results.append({
                    "variant_id": variant['id'],
                    "status": "review",
                    "notes": ["Moderation parsing failed"],
                    "confidence": "low"
                })
        
        # Overall moderation status
        overall_status = "pass"
        if any(r["status"] == "reject" for r in moderation_results):
            overall_status = "reject"
        elif any(r["status"] == "review" for r in moderation_results):
            overall_status = "review"
        
        logger.info(f"Moderation completed with overall status: {overall_status}")
        return {
            "status": overall_status,
            "variants": moderation_results,
            "notes": []
        }
        
    except Exception as e:
        logger.error(f"Content moderation failed: {e}")
        return {
            "status": "review",
            "variants": [],
            "notes": ["Moderation failed"]
        }



def create_fallback_variants(summary: str, opinion: str, tone: str, job_id: str) -> List[Dict[str, Any]]:
    """Create fallback variants when AI generation fails."""
    logger.info("Creating fallback post variants")
    base_text = f"Interesting article about {summary[:100]}... {opinion} #AI #Tech #Innovation"
    
    return [
        {
            "id": "A",
            "text": base_text,
            "hashtags": ["#AI", "#Tech", "#Innovation"],
            "suggested_comment": "What are your thoughts on this?",
            "alt_text": "AI technology illustration",
            "image_path": f"/api/v1/images/{job_id}/A.png"
        },
        {
            "id": "B",
            "text": f"Another perspective: {summary[:100]}... {opinion} #Future #Digital #Trends",
            "hashtags": ["#Future", "#Digital", "#Trends"],
            "suggested_comment": "How does this impact your industry?",
            "alt_text": "Digital transformation concept",
            "image_path": f"/api/v1/images/{job_id}/B.png"
        }
    ]




async def regenerate_content(job_id: str, regenerate_type: str, variant: str) -> bool:
    """Regenerate specific content for a variant."""
    logger.info(f"Regenerating content for job_id: {job_id}, type: {regenerate_type}, variant: {variant}")
    try:
        # Get job files
        job_files = get_job_files(job_id)
        if not job_files:
            return False
        
        # Read current result
        result = read_json(job_files["result"])
        if not result:
            return False
        
        # Find the variant
        variant_data = None
        for v in result["post_variants"]:
            if v["id"] == variant:
                variant_data = v
                break
        
        if not variant_data:
            return False
        
        if regenerate_type in ["text", "both"]:
            # Regenerate text
            summary = ""
            with open(job_files["summary"], 'r', encoding='utf-8') as f:
                summary = f.read()
            
            # Read job details for regeneration, capture fields, and generate
            with Session(engine) as session:
                job = session.exec(select(Job).where(Job.job_id == job_id)).first()
                if job:
                    job_opinion = job.opinion
                    job_tone = job.tone
                else:
                    job_opinion = ""
                    job_tone = "professional"

            new_variants = await generate_post_variants_with_langchain(
                summary,
                [],
                job_opinion,
                job_tone,
                job_id,
            )
            # Update the specific variant
            for new_v in new_variants:
                if new_v["id"] == variant:
                    variant_data.update(new_v)
                    break
        
        if regenerate_type in ["image", "both"]:
            # Regenerate image
            with Session(engine) as session:
                job = session.exec(select(Job).where(Job.job_id == job_id)).first()
                image_options = job.get_image_options() if job else {}
            
            # Generate new image prompt
            messages = create_image_prompt_messages(
                variant_data['text'][:100],
                image_options.get('style', 'photographic'),
                image_options.get('negative_prompt', 'no text, no logos')
            )
            
            image_prompt = await provider.generate_text(
                prompt=str(messages[-1].content),
                max_tokens=200,
                temperature=0.5
            )
            try:
                logger.debug(f"Regenerating image for job={job_id} variant={variant} provider={provider.__class__.__name__} prompt={image_prompt}")
                image_data = await provider.generate_image(
                    prompt=image_prompt,
                    negative_prompt=image_options.get('negative_prompt', 'no text, no logos'),
                    size=image_options.get('aspect_ratio', '16:9'),
                    job_id=job_id
                )
            except Exception as e:
                logger.exception(f"Failed to regenerate image for job={job_id} variant={variant} provider={provider.__class__.__name__} prompt={image_prompt} options={image_options}: {e}")
                raise
            # Save new image
            from pathlib import Path
            image_path = Path(f"./tmp/{job_id}/images/{variant}.png")
            await save_image(image_data, image_path)
            # Update variant with new image path (API URL)
            variant_data['image_path'] = f"/api/v1/images/{job_id}/{variant}.png"
        
        # Save updated result
        await save_json(result, job_files["result"])
        return True
        
    except Exception as e:
        logger.error(f"Regeneration failed for job {job_id}: {e}")
        return False


def publish_to_linkedin(job_id: str, variant: str, user_id: str) -> Dict[str, Any]:
    """Publish variant to LinkedIn (stubbed for development)."""
    logger.info(f"Publishing job_id: {job_id}, variant: {variant}, user_id: {user_id} to LinkedIn (simulated)")
    try:
        # In production, this would integrate with LinkedIn API
        # For now, return simulated success
        
        linkedin_post_id = f"linkedin_{job_id}_{variant}_{user_id}"
        
        logger.info(f"Simulated LinkedIn publish: {linkedin_post_id}")
        
        return {
            "job_id": job_id,
            "published": True,
            "linkedin_post_id": linkedin_post_id,
            "variant": variant,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"LinkedIn publish failed: {e}")
        return {
            "job_id": job_id,
            "published": False,
            "error": str(e)
        }

# Initialize database on import
create_db_and_tables()
