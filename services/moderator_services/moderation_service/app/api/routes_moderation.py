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


# =============================================================================
# IMAGE PROCESSING PIPELINE ENDPOINT
# =============================================================================

class ImageProcessRequest(BaseModel):
    """Request for image processing pipeline"""
    image_data: str  # Base64 encoded image
    filename: Optional[str] = "image.jpg"
    context: Optional[Dict[str, Any]] = {}
    options: Optional[Dict[str, Any]] = {}


class ImageProcessResponse(BaseModel):
    """Response with processed image and moderation results"""
    success: bool
    decision: str = "approve"
    processed_image: Optional[str] = None  # Base64 encoded WebP
    original_size: int = 0
    processed_size: int = 0
    format: str = "webp"
    sanitized: bool = False
    compressed: bool = False
    threats_found: List[str] = []
    warnings: List[str] = []
    ocr_text: Optional[str] = None
    processing_time_ms: float = 0
    error: Optional[str] = None


@router.post("/image/process", response_model=ImageProcessResponse)
async def process_image(request: ImageProcessRequest):
    """
    Full image processing pipeline: Scan → Sanitize → Compress → OCR

    This endpoint:
    1. Receives image as base64
    2. Scans for security threats (hidden data, steganography, etc.)
    3. Sanitizes image (removes hidden data, re-encodes)
    4. Compresses to WebP ≤ 1MB
    5. Optionally extracts text via OCR
    6. Returns the PROCESSED image (safe to store) + moderation decision

    Use this endpoint when uploading ads to get back safe, compressed images.

    Example:
        POST /moderate/image/process
        {
            "image_data": "<base64 encoded image>",
            "filename": "photo.jpg",
            "options": {
                "sanitize": true,
                "compress": true,
                "target_size": 1048576,
                "output_format": "webp",
                "extract_text": true
            }
        }

    Returns:
        {
            "success": true,
            "decision": "approve",
            "processed_image": "<base64 encoded WebP>",
            "original_size": 5000000,
            "processed_size": 800000,
            "sanitized": true,
            "compressed": true,
            "threats_found": ["hidden_data"],
            "ocr_text": "Text from image..."
        }
    """
    import base64
    import io
    start_time = time.time()

    response = ImageProcessResponse(success=False)

    try:
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.image_data)
            response.original_size = len(image_bytes)
        except Exception as e:
            response.error = f"Invalid base64 image data: {e}"
            return response

        # Get options
        options = request.options or {}
        target_size = options.get('target_size', 1024 * 1024)  # 1MB default
        do_sanitize = options.get('sanitize', True)
        do_compress = options.get('compress', True)
        extract_text = options.get('extract_text', False)

        # Import security scanner
        try:
            from app.services.images.security import SecurityScanner
            from app.services.images.image_compressor import ImageCompressor
        except ImportError:
            # Fallback imports
            import sys
            from pathlib import Path
            services_dir = Path(__file__).parent.parent / "services" / "images"
            sys.path.insert(0, str(services_dir))
            from security import SecurityScanner
            from image_compressor import ImageCompressor

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            # Initialize scanner with full pipeline
            scanner = SecurityScanner(
                auto_sanitize=do_sanitize,
                auto_compress=do_compress,
                target_size=target_size
            )

            # Run the pipeline
            scan_result = scanner.scan(tmp_path)

            # Collect threat info
            if scan_result.ml_hidden and scan_result.ml_hidden.has_hidden_data:
                response.threats_found.append('hidden_data')
            if scan_result.ml_steg and scan_result.ml_steg.has_steganography:
                response.threats_found.append('steganography')
            if scan_result.ml_forensics and scan_result.ml_forensics.is_manipulated:
                response.threats_found.append('manipulation')

            # Get processed data
            processed_data = None
            if scan_result.compressed and scan_result.compressed_data:
                processed_data = scan_result.compressed_data
                response.compressed = True
            elif scan_result.sanitized and scan_result.sanitized_data:
                processed_data = scan_result.sanitized_data
            else:
                # Fallback to original
                processed_data = image_bytes

            response.sanitized = scan_result.sanitized
            response.processed_size = len(processed_data)

            # Encode processed image as base64
            response.processed_image = base64.b64encode(processed_data).decode('utf-8')

            # Collect warnings
            response.warnings = [w for w in scan_result.warnings if 'Sanitizer' in w or 'Compressor' in w]

            # Determine decision based on threats
            if len(response.threats_found) > 2:
                response.decision = 'review'
            elif scan_result.threat_level.value == 'critical':
                response.decision = 'review'  # Still allow but flag for review
            else:
                response.decision = 'approve'

            # OCR text extraction (optional)
            if extract_text:
                try:
                    from app.services.images.ocr_processor import ImageOCRProcessor
                    ocr = ImageOCRProcessor()
                    ocr_result = ocr.extract_text(io.BytesIO(processed_data))
                    if ocr_result and ocr_result.get('text'):
                        response.ocr_text = ocr_result['text']
                except Exception as ocr_err:
                    response.warnings.append(f"OCR failed: {ocr_err}")

            response.success = True

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        response.error = str(e)
        response.warnings.append(f"Processing failed: {e}")

    response.processing_time_ms = (time.time() - start_time) * 1000
    return response


# Alias for backward compatibility
@router.post("/image", response_model=ImageProcessResponse)
async def process_image_alias(request: ImageProcessRequest):
    """Alias for /image/process"""
    return await process_image(request)


# =============================================================================
# TEXT PROCESSING PIPELINE ENDPOINT
# =============================================================================

class TextProcessRequest(BaseModel):
    """Request for text processing pipeline"""
    title: str
    description: str
    category: Optional[str] = "general"
    language: Optional[str] = "auto"
    context: Optional[Dict[str, Any]] = {}


class TextProcessResponse(BaseModel):
    """Response with text moderation results"""
    success: bool
    decision: str = "approve"  # approve, review, block
    risk_level: str = "low"  # low, medium, high, critical
    global_score: float = 0.0
    category_scores: Dict[str, float] = {}
    flags: List[str] = []
    reasons: List[str] = []
    detected_language: Optional[str] = None
    intent: Optional[str] = None
    ai_insights: List[str] = []
    processing_time_ms: float = 0
    error: Optional[str] = None


@router.post("/text/process", response_model=TextProcessResponse)
async def process_text(request: TextProcessRequest):
    """
    Text processing and moderation pipeline.

    This endpoint:
    1. Detects language
    2. Analyzes intent and context
    3. Checks for toxicity, hate speech, violence, etc.
    4. Returns moderation decision with detailed scores

    Use this endpoint to moderate ad titles and descriptions.

    Example:
        POST /moderate/text/process
        {
            "title": "iPhone 15 for sale",
            "description": "Brand new, sealed box. Contact for details.",
            "category": "electronics",
            "language": "auto"
        }

    Returns:
        {
            "success": true,
            "decision": "approve",
            "risk_level": "low",
            "global_score": 0.05,
            "category_scores": {"toxicity": 0.01, "violence": 0.0, ...},
            "detected_language": "en",
            "intent": "legitimate_sale"
        }
    """
    start_time = time.time()

    response = TextProcessResponse(success=False)

    try:
        pipeline = get_pipeline()

        # Build user context
        user_context = {
            "category": request.category,
            "language": request.language,
            **(request.context or {})
        }

        # Run text moderation
        result = pipeline.moderate_text(
            title=request.title,
            description=request.description,
            category=request.category,
            user_context=user_context
        )

        response.success = True
        response.decision = result.get('decision', 'approve')
        response.risk_level = result.get('risk_level', 'low')
        response.global_score = result.get('global_score', 0.0)
        response.category_scores = result.get('category_scores', {})
        response.flags = result.get('flags', [])
        response.reasons = result.get('reasons', [])
        response.detected_language = result.get('detected_language')
        response.intent = result.get('intent')
        response.ai_insights = result.get('ai_insights', [])

    except Exception as e:
        response.error = str(e)

    response.processing_time_ms = (time.time() - start_time) * 1000
    return response


# Alias for text processing
@router.post("/text", response_model=TextProcessResponse)
async def process_text_alias(request: TextProcessRequest):
    """Alias for /text/process"""
    return await process_text(request)


# =============================================================================
# VIDEO PROCESSING PIPELINE ENDPOINT
# =============================================================================

class VideoProcessRequest(BaseModel):
    """Request for video processing pipeline"""
    video_data: Optional[str] = None  # Base64 encoded video (for small videos)
    video_url: Optional[str] = None   # URL to video file
    video_path: Optional[str] = None  # Local path to video file
    filename: Optional[str] = "video.mp4"
    context: Optional[Dict[str, Any]] = {}
    options: Optional[Dict[str, Any]] = {}


class VideoProcessResponse(BaseModel):
    """Response with video moderation results"""
    success: bool
    decision: str = "approve"  # approve, review, block
    risk_level: str = "low"
    global_score: float = 0.0

    # Video analysis results
    duration_seconds: float = 0.0
    frames_analyzed: int = 0
    audio_analyzed: bool = False

    # Content detection
    category_scores: Dict[str, float] = {}
    flags: List[str] = []
    reasons: List[str] = []

    # Detected content
    detected_objects: List[str] = []
    detected_text: List[str] = []  # Text from video frames
    detected_speech: Optional[str] = None  # Transcribed audio

    # Timeline of issues (timestamp: issue)
    timeline_issues: Dict[str, List[str]] = {}

    # Processing info
    processing_time_ms: float = 0
    warnings: List[str] = []
    error: Optional[str] = None


@router.post("/video/process", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest):
    """
    Video processing and moderation pipeline.

    This endpoint:
    1. Extracts frames at 2 FPS
    2. Analyzes each frame for NSFW, violence, weapons, etc.
    3. Extracts and transcribes audio
    4. Checks speech for toxicity
    5. Returns comprehensive moderation decision

    Note: Video processing can be slow. For long videos (>1 min),
    consider using /video/process-async for background processing.

    Example:
        POST /moderate/video/process
        {
            "video_url": "https://example.com/video.mp4",
            "options": {
                "fps": 2,
                "analyze_audio": true,
                "max_duration": 60
            }
        }

    Returns:
        {
            "success": true,
            "decision": "approve",
            "duration_seconds": 45.2,
            "frames_analyzed": 90,
            "detected_objects": ["person", "car"],
            "detected_speech": "Hello, this is a test video..."
        }
    """
    start_time = time.time()

    response = VideoProcessResponse(success=False)

    try:
        # Get options
        options = request.options or {}
        fps = options.get('fps', 2)
        analyze_audio = options.get('analyze_audio', True)
        max_duration = options.get('max_duration', 60)  # Max 60 seconds by default

        # Determine video source
        video_path = None
        temp_video = None

        if request.video_path and os.path.exists(request.video_path):
            video_path = request.video_path
        elif request.video_url:
            # Download video to temp file
            import urllib.request
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            try:
                urllib.request.urlretrieve(request.video_url, temp_video.name)
                video_path = temp_video.name
            except Exception as e:
                response.error = f"Failed to download video: {e}"
                return response
        elif request.video_data:
            # Decode base64 video
            import base64
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            try:
                video_bytes = base64.b64decode(request.video_data)
                temp_video.write(video_bytes)
                temp_video.close()
                video_path = temp_video.name
            except Exception as e:
                response.error = f"Invalid base64 video data: {e}"
                return response
        else:
            response.error = "No video provided. Use video_path, video_url, or video_data."
            return response

        try:
            # Import video moderation pipeline
            try:
                from app.services.video_moderation_pipeline import VideoModerationPipeline
            except ImportError:
                from app.services.video.video_moderation_pipeline import VideoModerationPipeline

            # Initialize and run pipeline
            video_pipeline = VideoModerationPipeline()
            result = video_pipeline.moderate_video(
                video_path,
                fps=fps,
                analyze_audio=analyze_audio,
                max_duration=max_duration
            )

            # Map results to response
            response.success = result.get('success', True)
            response.decision = result.get('decision', 'approve')
            response.risk_level = result.get('risk_level', 'low')
            response.global_score = result.get('global_score', 0.0)
            response.duration_seconds = result.get('duration', 0.0)
            response.frames_analyzed = result.get('frames_analyzed', 0)
            response.audio_analyzed = result.get('audio_analyzed', False)
            response.category_scores = result.get('category_scores', {})
            response.flags = result.get('flags', [])
            response.reasons = result.get('reasons', [])
            response.detected_objects = result.get('detected_objects', [])
            response.detected_text = result.get('detected_text', [])
            response.detected_speech = result.get('transcript')
            response.timeline_issues = result.get('timeline_issues', {})
            response.warnings = result.get('warnings', [])

        finally:
            # Clean up temp file
            if temp_video and os.path.exists(temp_video.name):
                os.unlink(temp_video.name)

    except Exception as e:
        response.error = str(e)
        response.warnings.append(f"Video processing failed: {e}")

    response.processing_time_ms = (time.time() - start_time) * 1000
    return response


# Alias for video processing
@router.post("/video", response_model=VideoProcessResponse)
async def process_video_alias(request: VideoProcessRequest):
    """Alias for /video/process"""
    return await process_video(request)


# Async video processing for long videos
@router.post("/video/process-async")
async def process_video_async(request: VideoProcessRequest, background_tasks: BackgroundTasks):
    """
    Async video processing for long videos.

    Returns a job_id immediately. Check status with /job/{job_id}

    Example:
        POST /moderate/video/process-async
        {"video_url": "https://example.com/long_video.mp4"}

    Returns:
        {"job_id": "abc123", "status": "processing"}
    """
    job_id = str(uuid.uuid4())

    # Store initial job status
    queue = get_queue_client()
    await queue.set_job_status(job_id, {
        "status": "processing",
        "type": "video",
        "started_at": datetime.utcnow().isoformat()
    })

    async def process_in_background():
        try:
            result = await process_video(request)
            await queue.set_job_status(job_id, {
                "status": "completed",
                "result": result.dict(),
                "completed_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            await queue.set_job_status(job_id, {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })

    background_tasks.add_task(process_in_background)

    return {
        "job_id": job_id,
        "status": "processing"
    }


# =============================================================================
# REALTIME AD SCANNER ENDPOINT
# =============================================================================

class RealtimeScannerRequest(BaseModel):
    """Request for realtime ad scanning"""
    mode: str = "incremental"  # incremental, full, single
    ad_id: Optional[str] = None  # For single ad scan
    company_id: Optional[str] = None  # Filter by company
    category: Optional[str] = None  # Filter by category
    limit: Optional[int] = 100  # Max ads to scan per run
    skip_cached: bool = True  # Skip recently scanned ads
    cache_ttl_hours: int = 24  # How long to cache scan results
    options: Optional[Dict[str, Any]] = {}


class AdScanResult(BaseModel):
    """Result for a single ad scan"""
    ad_id: str
    title: str
    decision: str = "approve"
    risk_level: str = "low"
    global_score: float = 0.0
    flags: List[str] = []
    reasons: List[str] = []
    suggested_action: str = "none"  # none, review, pause, block, delete
    scanned_at: str = ""


class RealtimeScannerResponse(BaseModel):
    """Response from realtime scanner"""
    success: bool
    mode: str
    total_ads_scanned: int = 0
    clean_ads: int = 0
    flagged_ads: int = 0
    blocked_ads: int = 0

    # Detailed results
    results: List[AdScanResult] = []
    flagged_details: List[AdScanResult] = []

    # Performance metrics
    scan_time_ms: float = 0
    ads_per_second: float = 0

    # Scanner status
    last_scan_timestamp: Optional[str] = None
    next_scan_estimate: Optional[str] = None
    cache_hits: int = 0
    cache_misses: int = 0

    # Errors
    errors: List[str] = []
    warnings: List[str] = []


# Import scalable scanner
try:
    from app.services.scalable_scanner import (
        ScalableRealtimeScanner,
        ScannerConfig,
        ScanPriority,
        get_scanner,
        shutdown_scanner
    )
    SCALABLE_SCANNER_AVAILABLE = True
except ImportError:
    SCALABLE_SCANNER_AVAILABLE = False

# Fallback in-memory cache
_scan_cache: Dict[str, Dict] = {}
_last_full_scan: Optional[datetime] = None


@router.post("/realtimescanner", response_model=RealtimeScannerResponse)
async def realtime_scanner(request: RealtimeScannerRequest):
    """
    Realtime Ad Scanner - High-performance, scalable ad scanning.

    Features:
    - Async/concurrent processing with worker pools
    - Redis-based distributed caching (with in-memory fallback)
    - Batch processing for database efficiency
    - Circuit breaker pattern for resilience
    - Rate limiting and backpressure
    - Metrics and monitoring

    This endpoint provides continuous monitoring of all ads:
    1. Scans ad titles and descriptions for policy violations
    2. Checks for newly prohibited content
    3. Identifies ads that need review
    4. Suggests actions (pause, block, delete, notify owner)

    Modes:
    - incremental: Only scan ads changed since last scan
    - full: Scan all ads in the system
    - single: Scan a specific ad by ID

    Performance:
    - Can handle 100+ ads/second with proper configuration
    - Scales horizontally with Redis caching
    - Worker pool size adjusts to CPU count

    Example:
        POST /moderate/realtimescanner
        {
            "mode": "incremental",
            "limit": 100,
            "skip_cached": true
        }

    Returns:
        {
            "success": true,
            "total_ads_scanned": 100,
            "clean_ads": 95,
            "flagged_ads": 5,
            "flagged_details": [...],
            "scan_time_ms": 2500.5,
            "ads_per_second": 40.0
        }
    """
    start_time = time.time()

    # Use scalable scanner if available
    if SCALABLE_SCANNER_AVAILABLE:
        try:
            pipeline = get_pipeline()
            scanner = await get_scanner(pipeline)

            # Single ad scan
            if request.mode == "single" and request.ad_id:
                result = await scanner.scan_single(request.ad_id)

                return RealtimeScannerResponse(
                    success=True,
                    mode="single",
                    total_ads_scanned=1,
                    clean_ads=1 if result.get('decision') == 'approve' else 0,
                    flagged_ads=1 if result.get('decision') != 'approve' else 0,
                    blocked_ads=1 if result.get('decision') == 'block' else 0,
                    results=[AdScanResult(
                        ad_id=request.ad_id,
                        title=result.get('title', ''),
                        decision=result.get('decision', 'approve'),
                        risk_level=result.get('risk_level', 'low'),
                        global_score=result.get('global_score', 0.0),
                        flags=result.get('flags', []),
                        reasons=result.get('reasons', []),
                        suggested_action=_determine_action(result),
                        scanned_at=datetime.utcnow().isoformat()
                    )],
                    scan_time_ms=(time.time() - start_time) * 1000,
                    last_scan_timestamp=datetime.utcnow().isoformat()
                )

            # Batch scan
            result = await scanner.scan_batch(
                mode=request.mode,
                limit=request.limit or 100,
                company_id=request.company_id,
                category=request.category,
                skip_cached=request.skip_cached
            )

            # Convert to response format
            flagged_details = []
            for r in result.get('flagged_details', []):
                flagged_details.append(AdScanResult(
                    ad_id=r.get('ad_id', ''),
                    title=r.get('title', '')[:100],
                    decision=r.get('decision', 'approve'),
                    risk_level=r.get('risk_level', 'low'),
                    global_score=r.get('global_score', 0.0),
                    flags=r.get('flags', []),
                    reasons=r.get('reasons', []),
                    suggested_action=_determine_action(r),
                    scanned_at=datetime.utcnow().isoformat()
                ))

            return RealtimeScannerResponse(
                success=result.get('success', True),
                mode=request.mode,
                total_ads_scanned=result.get('total_ads_scanned', 0),
                clean_ads=result.get('clean_ads', 0),
                flagged_ads=result.get('flagged_ads', 0),
                blocked_ads=result.get('blocked_ads', 0),
                flagged_details=flagged_details,
                scan_time_ms=result.get('scan_time_ms', 0),
                ads_per_second=result.get('ads_per_second', 0),
                cache_hits=result.get('cache_hits', 0),
                cache_misses=result.get('cache_misses', 0),
                last_scan_timestamp=result.get('last_scan_timestamp'),
                errors=result.get('errors', [])
            )

        except Exception as e:
            # Fall back to basic scanner
            print(f"[Scanner] Scalable scanner failed, using fallback: {e}")

    # Fallback to basic scanner
    global _scan_cache, _last_full_scan

    response = RealtimeScannerResponse(
        success=False,
        mode=request.mode
    )

    try:
        pipeline = get_pipeline()

        # Load ads from database/filesystem
        ads_to_scan = await _load_ads_for_scanning(
            mode=request.mode,
            ad_id=request.ad_id,
            company_id=request.company_id,
            category=request.category,
            limit=request.limit
        )

        cache_hits = 0
        cache_misses = 0
        results = []
        flagged = []
        blocked = []

        for ad in ads_to_scan:
            ad_id = ad.get('id', ad.get('ad_id', ''))

            # Check cache
            if request.skip_cached and ad_id in _scan_cache:
                cached = _scan_cache[ad_id]
                cache_age_hours = (time.time() - cached.get('timestamp', 0)) / 3600

                if cache_age_hours < request.cache_ttl_hours:
                    cache_hits += 1
                    # Use cached result
                    if cached.get('decision') != 'approve':
                        flagged.append(AdScanResult(**cached['result']))
                    continue

            cache_misses += 1

            # Scan the ad
            try:
                scan_result = await _scan_single_ad(pipeline, ad)

                result = AdScanResult(
                    ad_id=ad_id,
                    title=ad.get('title', '')[:100],
                    decision=scan_result.get('decision', 'approve'),
                    risk_level=scan_result.get('risk_level', 'low'),
                    global_score=scan_result.get('global_score', 0.0),
                    flags=scan_result.get('flags', []),
                    reasons=scan_result.get('reasons', []),
                    suggested_action=_determine_action(scan_result),
                    scanned_at=datetime.utcnow().isoformat()
                )

                results.append(result)

                # Cache the result
                _scan_cache[ad_id] = {
                    'timestamp': time.time(),
                    'decision': result.decision,
                    'result': result.dict()
                }

                # Categorize
                if result.decision == 'block':
                    blocked.append(result)
                    flagged.append(result)
                elif result.decision == 'review' or result.flags:
                    flagged.append(result)

            except Exception as e:
                response.errors.append(f"Failed to scan ad {ad_id}: {str(e)}")

        # Update response
        response.success = True
        response.total_ads_scanned = len(results)
        response.clean_ads = len(results) - len(flagged)
        response.flagged_ads = len(flagged)
        response.blocked_ads = len(blocked)
        response.results = results[:50]  # Limit response size
        response.flagged_details = flagged
        response.cache_hits = cache_hits
        response.cache_misses = cache_misses

        # Update scan timestamp
        if request.mode == 'full':
            _last_full_scan = datetime.utcnow()

        response.last_scan_timestamp = datetime.utcnow().isoformat()

    except Exception as e:
        response.errors.append(f"Scanner error: {str(e)}")

    # Calculate performance metrics
    elapsed_ms = (time.time() - start_time) * 1000
    response.scan_time_ms = round(elapsed_ms, 2)

    if elapsed_ms > 0 and response.total_ads_scanned > 0:
        response.ads_per_second = round(response.total_ads_scanned / (elapsed_ms / 1000), 2)

    return response


@router.post("/realtimescanner/start")
async def start_background_scanner(background_tasks: BackgroundTasks):
    """
    Start continuous background scanning.

    Returns a scanner_id that can be used to check status or stop.
    """
    scanner_id = f"scanner-{uuid.uuid4().hex[:8]}"

    queue = get_queue_client()
    await queue.set_job_status(scanner_id, {
        "status": "running",
        "type": "realtime_scanner",
        "started_at": datetime.utcnow().isoformat(),
        "ads_scanned": 0,
        "flagged": 0
    })

    async def continuous_scan():
        """Background task for continuous scanning"""
        total_scanned = 0
        total_flagged = 0

        while True:
            try:
                # Check if scanner should stop
                status = await queue.get_job_status(scanner_id)
                if status and status.get('status') == 'stopped':
                    break

                # Run incremental scan
                result = await realtime_scanner(RealtimeScannerRequest(
                    mode="incremental",
                    limit=50,
                    skip_cached=True
                ))

                total_scanned += result.total_ads_scanned
                total_flagged += result.flagged_ads

                # Update status
                await queue.set_job_status(scanner_id, {
                    "status": "running",
                    "ads_scanned": total_scanned,
                    "flagged": total_flagged,
                    "last_run": datetime.utcnow().isoformat()
                })

                # Wait before next scan
                import asyncio
                await asyncio.sleep(30)  # Scan every 30 seconds

            except Exception as e:
                await queue.set_job_status(scanner_id, {
                    "status": "error",
                    "error": str(e),
                    "ads_scanned": total_scanned,
                    "flagged": total_flagged
                })
                break

    background_tasks.add_task(continuous_scan)

    return {
        "scanner_id": scanner_id,
        "status": "started",
        "message": "Background scanner started. Check status at /moderate/realtimescanner/status/{scanner_id}"
    }


@router.get("/realtimescanner/status/{scanner_id}")
async def get_scanner_status(scanner_id: str):
    """Get status of background scanner"""
    queue = get_queue_client()
    status = await queue.get_job_status(scanner_id)

    if not status:
        raise HTTPException(status_code=404, detail="Scanner not found")

    return status


@router.post("/realtimescanner/stop/{scanner_id}")
async def stop_scanner(scanner_id: str):
    """Stop a running background scanner"""
    queue = get_queue_client()

    status = await queue.get_job_status(scanner_id)
    if not status:
        raise HTTPException(status_code=404, detail="Scanner not found")

    await queue.set_job_status(scanner_id, {
        **status,
        "status": "stopped",
        "stopped_at": datetime.utcnow().isoformat()
    })

    return {"scanner_id": scanner_id, "status": "stopped"}


@router.get("/realtimescanner/stats")
async def get_scanner_stats():
    """
    Get comprehensive scanner statistics and metrics.

    Returns:
    - Performance metrics (throughput, timing)
    - Cache statistics (hits, misses, hit rate)
    - Queue status
    - Error counts
    - Health indicators
    """
    global _scan_cache, _last_full_scan

    # Try scalable scanner first
    if SCALABLE_SCANNER_AVAILABLE:
        try:
            pipeline = get_pipeline()
            scanner = await get_scanner(pipeline)

            metrics = scanner.get_metrics()
            cache_stats = await scanner.get_cache_stats()
            status = scanner.get_status()

            return {
                "scanner_type": "scalable",
                "status": status,
                "metrics": metrics,
                "cache": cache_stats,
                "health": {
                    "running": status.get("running", False),
                    "circuit_breaker": status.get("circuit_breaker", "unknown"),
                    "workers_active": status.get("workers", 0),
                    "queue_depth": status.get("queue_size", 0),
                }
            }
        except Exception as e:
            pass  # Fall back to basic stats

    # Fallback stats
    total_cached = len(_scan_cache)
    flagged_in_cache = sum(1 for v in _scan_cache.values() if v.get('decision') != 'approve')

    return {
        "scanner_type": "basic",
        "cache_size": total_cached,
        "cached_flagged": flagged_in_cache,
        "cached_clean": total_cached - flagged_in_cache,
        "last_full_scan": _last_full_scan.isoformat() if _last_full_scan else None,
        "cache_memory_estimate_kb": round(total_cached * 0.5, 2)  # Rough estimate
    }


# =============================================================================
# HELPER FUNCTIONS FOR REALTIME SCANNER
# =============================================================================

async def _load_ads_for_scanning(
    mode: str,
    ad_id: Optional[str] = None,
    company_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Load ads from the database/filesystem for scanning.

    This function connects to your ad storage system.
    """
    ads = []

    try:
        # Path to ads data directory
        import glob
        import json
        from pathlib import Path

        # Adjust this path to your actual ads storage
        ads_base_path = Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "companies"

        if not ads_base_path.exists():
            # Try alternative path
            ads_base_path = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/data/companies")

        if mode == "single" and ad_id:
            # Find specific ad
            for meta_file in ads_base_path.rglob("*/ads/*/meta.json"):
                try:
                    with open(meta_file, 'r') as f:
                        ad_data = json.load(f)
                        if ad_data.get('id') == ad_id or ad_data.get('ad_id') == ad_id:
                            ads.append(ad_data)
                            break
                except:
                    pass
        else:
            # Scan all ads or filter
            for meta_file in ads_base_path.rglob("*/ads/*/meta.json"):
                if len(ads) >= limit:
                    break

                try:
                    with open(meta_file, 'r') as f:
                        ad_data = json.load(f)

                        # Apply filters
                        if company_id and ad_data.get('company') != company_id:
                            continue
                        if category and ad_data.get('category') != category:
                            continue

                        ads.append(ad_data)
                except:
                    pass

        # Also try SQLite database if available
        try:
            import sqlite3
            db_path = Path(__file__).parent.parent.parent.parent.parent.parent / "database" / "adsphere.db"

            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM ads WHERE status = 'active'"
                params = []

                if mode == "single" and ad_id:
                    query += " AND (id = ? OR ad_id = ?)"
                    params.extend([ad_id, ad_id])
                if company_id:
                    query += " AND company_id = ?"
                    params.append(company_id)
                if category:
                    query += " AND category = ?"
                    params.append(category)

                query += f" LIMIT {limit}"

                cursor.execute(query, params)

                for row in cursor.fetchall():
                    ads.append(dict(row))

                conn.close()
        except Exception as db_err:
            pass  # Database not available, use file-based ads

    except Exception as e:
        print(f"Error loading ads: {e}")

    return ads


async def _scan_single_ad(pipeline, ad: Dict) -> Dict:
    """Scan a single ad and return results"""
    title = ad.get('title', '')
    description = ad.get('description', '')
    category = ad.get('category', 'general')

    # Run text moderation
    result = pipeline.moderate_text(
        title=title,
        description=description,
        category=category,
        user_context={
            'ad_id': ad.get('id', ad.get('ad_id')),
            'company': ad.get('company', ad.get('company_id')),
            'source': 'realtime_scanner'
        }
    )

    return result


def _determine_action(scan_result: Dict) -> str:
    """Determine suggested action based on scan results"""
    decision = scan_result.get('decision', 'approve')
    risk_level = scan_result.get('risk_level', 'low')
    flags = scan_result.get('flags', [])

    # Critical violations - immediate block
    critical_flags = {'violence', 'weapons', 'illegal_drugs', 'child_safety', 'terrorism'}
    if critical_flags.intersection(set(flags)):
        return 'block_and_notify'

    # High risk - block pending review
    if decision == 'block' or risk_level == 'critical':
        return 'block'

    # Medium risk - pause and review
    if decision == 'review' or risk_level == 'high':
        return 'pause_for_review'

    # Low risk flags - notify owner
    if flags and risk_level == 'medium':
        return 'notify_owner'

    # Clean
    return 'none'


# =============================================================================
# ADDITIONAL HIGH-PERFORMANCE SCANNER ENDPOINTS
# =============================================================================

@router.post("/realtimescanner/enqueue")
async def enqueue_ad_for_scanning(
    ad_id: str,
    priority: str = "normal",
    background_tasks: BackgroundTasks = None
):
    """
    Enqueue a specific ad for scanning (async).

    Use this when:
    - A new ad is posted
    - A user reports an ad
    - An ad is edited

    Priority levels:
    - urgent: Report/complaint triggered (processed first)
    - high: New ad
    - normal: Periodic rescan
    - low: Background scan

    Example:
        POST /moderate/realtimescanner/enqueue?ad_id=AD-123&priority=high
    """
    if not SCALABLE_SCANNER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Scalable scanner not available"
        )

    priority_map = {
        "urgent": ScanPriority.URGENT,
        "high": ScanPriority.HIGH,
        "normal": ScanPriority.NORMAL,
        "low": ScanPriority.LOW,
    }

    scan_priority = priority_map.get(priority.lower(), ScanPriority.NORMAL)

    try:
        pipeline = get_pipeline()
        scanner = await get_scanner(pipeline)

        success = await scanner.enqueue(
            ad_id=ad_id,
            priority=scan_priority
        )

        if success:
            return {
                "success": True,
                "ad_id": ad_id,
                "priority": priority,
                "message": "Ad enqueued for scanning"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Queue is full, try again later"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue: {str(e)}"
        )


@router.post("/realtimescanner/bulk-enqueue")
async def bulk_enqueue_ads(
    ad_ids: List[str],
    priority: str = "normal"
):
    """
    Enqueue multiple ads for scanning.

    Example:
        POST /moderate/realtimescanner/bulk-enqueue
        {
            "ad_ids": ["AD-1", "AD-2", "AD-3"],
            "priority": "high"
        }
    """
    if not SCALABLE_SCANNER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Scalable scanner not available"
        )

    priority_map = {
        "urgent": ScanPriority.URGENT,
        "high": ScanPriority.HIGH,
        "normal": ScanPriority.NORMAL,
        "low": ScanPriority.LOW,
    }

    scan_priority = priority_map.get(priority.lower(), ScanPriority.NORMAL)

    try:
        pipeline = get_pipeline()
        scanner = await get_scanner(pipeline)

        enqueued = 0
        failed = 0

        for ad_id in ad_ids[:1000]:  # Limit to 1000
            success = await scanner.enqueue(
                ad_id=ad_id,
                priority=scan_priority
            )
            if success:
                enqueued += 1
            else:
                failed += 1

        return {
            "success": True,
            "enqueued": enqueued,
            "failed": failed,
            "total_requested": len(ad_ids)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bulk enqueue failed: {str(e)}"
        )


@router.get("/realtimescanner/health")
async def get_scanner_health():
    """
    Get scanner health status for monitoring/alerting.

    Returns a simple health check suitable for load balancers
    and monitoring systems.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    if SCALABLE_SCANNER_AVAILABLE:
        try:
            pipeline = get_pipeline()
            scanner = await get_scanner(pipeline)
            status = scanner.get_status()

            # Check worker health
            health["checks"]["workers"] = {
                "status": "ok" if status.get("running") else "degraded",
                "count": status.get("workers", 0)
            }

            # Check circuit breaker
            cb_state = status.get("circuit_breaker", "unknown")
            health["checks"]["circuit_breaker"] = {
                "status": "ok" if cb_state == "closed" else "warning",
                "state": cb_state
            }

            # Check queue
            queue_size = status.get("queue_size", 0)
            health["checks"]["queue"] = {
                "status": "ok" if queue_size < 5000 else "warning",
                "depth": queue_size
            }

            # Overall status
            if not status.get("running"):
                health["status"] = "unhealthy"
            elif cb_state != "closed" or queue_size >= 5000:
                health["status"] = "degraded"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
    else:
        health["checks"]["scalable_scanner"] = {
            "status": "unavailable",
            "message": "Using basic scanner"
        }

    return health


@router.post("/realtimescanner/clear-cache")
async def clear_scanner_cache():
    """
    Clear the scanner cache.

    Use this after:
    - Policy changes
    - Model updates
    - When forcing a full rescan
    """
    global _scan_cache

    cleared = 0

    if SCALABLE_SCANNER_AVAILABLE:
        try:
            pipeline = get_pipeline()
            scanner = await get_scanner(pipeline)
            cleared = await scanner.cache.clear()
        except:
            pass

    # Also clear fallback cache
    fallback_cleared = len(_scan_cache)
    _scan_cache.clear()

    return {
        "success": True,
        "cleared": cleared + fallback_cleared,
        "message": "Cache cleared successfully"
    }


@router.get("/realtimescanner/config")
async def get_scanner_config():
    """Get current scanner configuration"""
    if SCALABLE_SCANNER_AVAILABLE:
        try:
            pipeline = get_pipeline()
            scanner = await get_scanner(pipeline)
            config = scanner.config

            return {
                "max_workers": config.max_workers,
                "batch_size": config.batch_size,
                "cache_backend": config.cache_backend,
                "cache_ttl_seconds": config.cache_ttl_seconds,
                "max_requests_per_second": config.max_requests_per_second,
                "circuit_breaker_threshold": config.circuit_breaker_threshold,
            }
        except:
            pass

    return {
        "scanner_type": "basic",
        "message": "Using basic scanner without advanced configuration"
    }

