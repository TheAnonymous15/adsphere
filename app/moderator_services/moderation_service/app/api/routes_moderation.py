"""
Moderation API routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from app.models.schemas import (
    ModerationRequest,
    ModerationResponse,
    CategoryScores,
    JobStatusResponse
)
from app.services.master_pipeline import MasterModerationPipeline
from app.infra.queue_client import QueueClient
import time
import uuid
from datetime import datetime
import os
import tempfile
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

# Initialize master pipeline (singleton)
master_pipeline = None

# Queue client singleton
queue_client = None


def get_queue_client():
    """Get or initialize queue client"""
    global queue_client
    if queue_client is None:
        queue_client = QueueClient()
    return queue_client


def get_pipeline():
    """Get or initialize master pipeline"""
    global master_pipeline
    if master_pipeline is None:
        master_pipeline = MasterModerationPipeline()
    return master_pipeline


@router.post("/realtime", response_model=ModerationResponse)
async def moderate_realtime(request: ModerationRequest):
    """
    Realtime moderation endpoint.

    Performs synchronous moderation of text and media.
    Returns immediate decision: approve, review, or block.

    This is the PRIMARY endpoint that your PHP system should call.

    Flow:
    1. Text moderation (always)
    2. Image moderation (if images provided)
    3. Video moderation (if videos provided) - NOTE: May be slow
    4. Aggregate all scores
    5. Return final decision
    """
    start_time = time.time()
    audit_id = f"mod-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:12]}"

    try:
        pipeline = get_pipeline()

        # Extract user context
        user_context = {
            "user_id": request.user.id if request.user else None,
            "company": request.user.company if request.user else None,
            "ad_id": request.context.ad_id if request.context else None,
            "source": request.context.source if request.context else "api",
            "ip": request.context.ip if request.context else None
        }

        # Step 1: Text moderation (always run)
        result = pipeline.moderate_text(
            title=request.title,
            description=request.description,
            category=request.category,
            user_context=user_context
        )

        # If text is already blocked, return immediately (no need to check media)
        if result['decision'] == 'block':
            return ModerationResponse(
                success=True,
                decision=result['decision'],
                global_score=result.get('global_score', 0.0),
                risk_level=result['risk_level'],
                category_scores=CategoryScores(**result['category_scores']),
                flags=result['flags'],
                reasons=result['reasons'],
                ai_sources=result.get('ai_sources', {}),
                audit_id=result['audit_id'],
                processing_time=result['processing_time'],
                timestamp=datetime.utcnow()
            )

        # Step 2: Process media if provided
        media_results = []
        if request.media:
            for media_item in request.media[:4]:  # Limit to 4 items
                if not media_item.url:
                    continue

                media_path = media_item.url

                # Check if file exists (for local paths)
                if not media_path.startswith('http') and not os.path.exists(media_path):
                    result['reasons'].append(f"Media file not found: {os.path.basename(media_path)}")
                    continue

                if media_item.type == "image":
                    # Run image moderation
                    try:
                        image_result = pipeline.moderate_image(media_path, user_context)
                        media_results.append({
                            'type': 'image',
                            'path': media_path,
                            'result': image_result
                        })
                    except Exception as e:
                        result['reasons'].append(f"Image analysis failed: {str(e)}")

                elif media_item.type == "video":
                    # Run video moderation (can be slow!)
                    try:
                        from app.services.video_moderation_pipeline import VideoModerationPipeline
                        video_pipeline = VideoModerationPipeline()
                        video_result = video_pipeline.moderate_video(media_path)
                        media_results.append({
                            'type': 'video',
                            'path': media_path,
                            'result': video_result
                        })
                    except Exception as e:
                        result['reasons'].append(f"Video analysis failed: {str(e)}")

        # Step 3: Aggregate media results with text results
        if media_results:
            # Merge category scores - take maximum of each category
            merged_scores = result['category_scores'].copy()
            merged_flags = set(result['flags'])
            merged_reasons = result['reasons'].copy()
            merged_ai_sources = result.get('ai_sources', {})

            for media_res in media_results:
                mr = media_res['result']
                if not mr.get('success', True):
                    continue

                # Merge category scores
                mr_scores = mr.get('category_scores', {})
                for key, value in mr_scores.items():
                    if key in merged_scores:
                        merged_scores[key] = max(merged_scores[key], value)
                    else:
                        merged_scores[key] = value

                # Merge flags
                merged_flags.update(mr.get('flags', []))

                # Merge reasons
                merged_reasons.extend(mr.get('reasons', []))

                # Merge AI sources
                for source_name, source_data in mr.get('ai_sources', {}).items():
                    merged_ai_sources[f"{media_res['type']}_{source_name}"] = source_data

            # Re-calculate decision based on merged scores
            from app.core.decision_engine import DecisionEngine
            decision, risk_level, new_flags, new_reasons = DecisionEngine.decide(merged_scores)
            global_score = DecisionEngine.calculate_global_score(merged_scores)

            # Update result
            result['category_scores'] = merged_scores
            result['flags'] = list(merged_flags.union(set(new_flags)))
            result['reasons'] = list(set(merged_reasons + new_reasons))
            result['ai_sources'] = merged_ai_sources
            result['decision'] = decision
            result['risk_level'] = risk_level
            result['global_score'] = global_score
            result['media_analyzed'] = len(media_results)

        # Build response
        response = ModerationResponse(
            success=True,
            decision=result['decision'],
            global_score=result.get('global_score', 0.0),
            risk_level=result['risk_level'],
            category_scores=CategoryScores(**result['category_scores']),
            flags=result['flags'],
            reasons=result['reasons'],
            ai_sources=result.get('ai_sources', {}),
            audit_id=result.get('audit_id', audit_id),
            processing_time=(time.time() - start_time) * 1000,
            timestamp=datetime.utcnow()
        )

        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Moderation failed: {str(e)}"
        )


@router.post("/video")
async def moderate_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Video moderation endpoint (async).

    Accepts video upload, enqueues processing job, returns job_id.
    Client polls /status/{job_id} for results.
    """
    job_id = f"job-{uuid.uuid4().hex}"

    try:
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{job_id}_{file.filename}")

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Enqueue job
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content)
        }

        success = queue_client.enqueue_video_job(job_id, temp_path, metadata)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to enqueue video job"
            )

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "message": "Video queued for moderation. Use GET /status/{job_id} to check progress."
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video upload failed: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    """
    Get moderation job status.
    """
    status = queue_client.get_job_status(job_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return JobStatusResponse(
        job_id=job_id,
        status=status,
        created_at=datetime.utcnow(),  # TODO: Store actual timestamps
        updated_at=datetime.utcnow()
    )


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get moderation result for completed job.
    """
    qc = get_queue_client()
    result = await qc.get_result(job_id)

    if not result:
        status = await qc.get_job_status(job_id)
        if status == "completed":
            raise HTTPException(
                status_code=410,
                detail="Result expired or not available"
            )
        elif status in ["queued", "running"]:
            raise HTTPException(
                status_code=202,
                detail=f"Job still processing (status: {status})"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

    return result


@router.post("/text")
async def moderate_text_only(
    title: str,
    description: str,
    category: str = "general"
):
    """
    Simple text-only moderation endpoint.

    Simpler alternative to /realtime for text-only content.
    """
    pipeline = get_pipeline()

    result = pipeline.moderate_text(
        title=title,
        description=description,
        category=category
    )

    return result


@router.post("/image", response_model=ModerationResponse)
async def moderate_image(file: UploadFile = File(...)):
    """
    Image moderation endpoint.

    Upload an image and get moderation results including:
    - NSFW detection
    - Violence detection
    - Weapon detection
    - Blood detection
    - OCR text extraction and moderation
    """
    pipeline = get_pipeline()

    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename or "upload.jpg")

    try:
        # Save file
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Moderate image
        result = pipeline.moderate_image(temp_path)

        # Clean up
        os.unlink(temp_path)
        os.rmdir(temp_dir)

        # Build response
        return ModerationResponse(
            success=result.get('success', True),
            decision=result.get('decision', 'review'),
            global_score=result.get('global_score', 0.0),
            risk_level=result.get('risk_level', 'low'),
            category_scores=CategoryScores(**result.get('category_scores', {})),
            flags=result.get('flags', []),
            reasons=result.get('reasons', []),
            ai_sources=result.get('ai_sources', {}),
            job=None,
            audit_id=result.get('audit_id', ''),
            processing_time=result.get('processing_time', 0.0),
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

        raise HTTPException(
            status_code=500,
            detail=f"Image moderation failed: {str(e)}"
        )


# =============================================================================
# YOUTUBE VIDEO MODERATION
# =============================================================================

class YouTubeRequest(BaseModel):
    """Request for YouTube video moderation"""
    url: str
    max_duration: Optional[int] = 300  # 5 minutes default
    batch_size: Optional[int] = 8
    audio_chunks: Optional[int] = 10


class YouTubeInfoResponse(BaseModel):
    """Response for YouTube video info check"""
    valid: bool
    video_id: Optional[str] = None
    title: Optional[str] = None
    channel: Optional[str] = None
    duration: Optional[float] = None
    view_count: Optional[int] = None
    is_live: Optional[bool] = None
    is_age_restricted: Optional[bool] = None
    warnings: List[str] = []
    can_process: bool = False
    error: Optional[str] = None


class YouTubeModerationResponse(BaseModel):
    """Response for YouTube video moderation"""
    success: bool
    youtube_info: Optional[Dict[str, Any]] = None
    moderation: Optional[Dict[str, Any]] = None
    download_time_ms: Optional[float] = None
    error: Optional[str] = None


@router.post("/youtube/check", response_model=YouTubeInfoResponse)
async def check_youtube_url(request: YouTubeRequest):
    """
    Quick check of YouTube video without downloading.

    Returns video info and basic metadata checks.
    Use this before full moderation to verify video is processable.

    Example:
        POST /moderate/youtube/check
        {"url": "https://youtube.com/watch?v=xxx"}
    """
    from app.services.video.youtube_processor import check_youtube_video

    try:
        result = await check_youtube_video(request.url)
        return YouTubeInfoResponse(**result)
    except Exception as e:
        return YouTubeInfoResponse(
            valid=False,
            error=str(e),
            can_process=False
        )


@router.post("/youtube/moderate", response_model=YouTubeModerationResponse)
async def moderate_youtube_url(request: YouTubeRequest):
    """
    Full moderation of YouTube video.

    Downloads video, extracts frames and audio, runs full moderation pipeline.

    Limits:
    - Max duration: 5 minutes (configurable)
    - No live streams

    Example:
        POST /moderate/youtube/moderate
        {
            "url": "https://youtube.com/watch?v=xxx",
            "max_duration": 300,
            "batch_size": 8,
            "audio_chunks": 10
        }

    Returns:
        - youtube_info: Video metadata (title, channel, duration)
        - moderation: Decision, risk level, flags, scores
    """
    from app.services.video.youtube_processor import moderate_youtube_video

    try:
        result = await moderate_youtube_video(
            url=request.url,
            max_duration=request.max_duration,
            batch_size=request.batch_size,
            audio_chunks=request.audio_chunks
        )
        return YouTubeModerationResponse(**result)
    except Exception as e:
        return YouTubeModerationResponse(
            success=False,
            error=str(e)
        )


@router.post("/youtube/moderate-async")
async def moderate_youtube_async(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """
    Async moderation of YouTube video (returns job ID immediately).

    Use this for long videos - check status with /job/{job_id}

    Example:
        POST /moderate/youtube/moderate-async
        {"url": "https://youtube.com/watch?v=xxx"}

    Returns:
        {"job_id": "...", "status": "processing"}
    """
    from app.services.video.youtube_processor import moderate_youtube_video

    job_id = str(uuid.uuid4())

    # Store initial job status
    queue = get_queue_client()
    await queue.set_job_status(job_id, {
        "status": "processing",
        "url": request.url,
        "started_at": datetime.utcnow().isoformat()
    })

    async def process_video():
        try:
            result = await moderate_youtube_video(
                url=request.url,
                max_duration=request.max_duration,
                batch_size=request.batch_size,
                audio_chunks=request.audio_chunks
            )
            await queue.set_job_status(job_id, {
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            await queue.set_job_status(job_id, {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })

    background_tasks.add_task(process_video)

    return {
        "job_id": job_id,
        "status": "processing",
        "url": request.url
    }
