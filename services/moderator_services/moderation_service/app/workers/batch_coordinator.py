import asyncio
import os
import tempfile
from collections import defaultdict
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor


# Global model instances (loaded once per process for efficiency)
_models = {}
_models_loaded = False


def _load_models():
    """Load all AI models once per worker process."""
    global _models, _models_loaded

    if _models_loaded:
        return _models

    # OCR Service
    try:
        from app.services.ocr_paddle import OCRService
        _models['ocr'] = OCRService()
        print("✓ OCR model loaded")
    except Exception as e:
        print(f"⚠ OCR not available: {e}")
        _models['ocr'] = None

    # NSFW Detector
    try:
        from app.services.nsfw_detector import NSFWDetector
        _models['nsfw'] = NSFWDetector()
        print("✓ NSFW detector loaded")
    except Exception as e:
        print(f"⚠ NSFW detector not available: {e}")
        _models['nsfw'] = None

    # Weapon Detector
    try:
        from app.services.yolo_weapons import WeaponDetector
        _models['weapon'] = WeaponDetector()
        print("✓ Weapon detector loaded")
    except Exception as e:
        print(f"⚠ Weapon detector not available: {e}")
        _models['weapon'] = None

    # Violence Detector
    try:
        from app.services.yolo_violence import ViolenceDetector
        _models['violence'] = ViolenceDetector()
        print("✓ Violence detector loaded")
    except Exception as e:
        print(f"⚠ Violence detector not available: {e}")
        _models['violence'] = None

    # Blood Detector
    try:
        from app.services.blood_detector import BloodDetector
        _models['blood'] = BloodDetector()
        print("✓ Blood detector loaded")
    except Exception as e:
        print(f"⚠ Blood detector not available: {e}")
        _models['blood'] = None

    # Text Moderator (Detoxify)
    try:
        from app.services.text_detoxify import DetoxifyService
        _models['detoxify'] = DetoxifyService()
        print("✓ Detoxify loaded")
    except Exception as e:
        print(f"⚠ Detoxify not available: {e}")
        _models['detoxify'] = None

    # Text Rules Engine
    try:
        from app.services.text_rules import TextRulesEngine
        _models['text_rules'] = TextRulesEngine()
        print("✓ Text rules engine loaded")
    except Exception as e:
        print(f"⚠ Text rules not available: {e}")
        _models['text_rules'] = None

    _models_loaded = True
    return _models


def _save_bytes_to_temp(asset_bytes: bytes, suffix: str = ".jpg") -> str:
    """Save bytes to a temporary file and return path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, asset_bytes)
    finally:
        os.close(fd)
    return path


def _cleanup_temp(path: str):
    """Remove temporary file."""
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except:
        pass


class BatchCoordinator:
    """
    High-level async batch orchestrator for multimodal moderation tasks.

    Responsibilities:
    - Accept new assets for processing
    - Batch tasks to pipelines (OCR/NSFW/Violence/Weapons/Policy)
    - Schedule workers with actual AI models
    - Return aggregated results via futures

    Pipelines:
    1. OCR Worker - Extract text from images
    2. NSFW Worker - Detect nudity/sexual content
    3. Violence Worker - Detect violence/blood
    4. Weapons Worker - Detect guns/knives
    5. Policy Worker - Apply text rules + reasoning
    """

    def __init__(
        self,
        batch_size: int = 8,
        max_wait_ms: int = 40,
        max_workers: int = 4
    ):
        # Batch behavior
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms / 1000
        self.max_workers = max_workers

        # Task futures for result delivery
        self._pending: Dict[str, asyncio.Future] = {}

        # Queue assets for batching
        self._batch_queue = asyncio.Queue()

        # Pipeline input buckets
        self._buckets = defaultdict(list)

        # Shutdown signaling
        self._closed = False

        # Locks to protect concurrent batch draining
        self._batch_lock = asyncio.Lock()

        # Thread pool for CPU-bound model inference
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        # Results accumulator
        self._results: Dict[str, Dict[str, Any]] = {}

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    async def schedule(self, task_id: str, asset_bytes: bytes, asset_type: str = "image"):
        """
        Schedule a new moderation request.

        Args:
            task_id: Unique identifier for this task
            asset_bytes: Raw bytes of the image/media
            asset_type: Type of asset ("image", "video_frame", "text")
        """
        if task_id in self._pending:
            return

        fut = asyncio.get_event_loop().create_future()
        self._pending[task_id] = fut
        self._results[task_id] = {"task_id": task_id, "type": asset_type}

        await self._batch_queue.put((task_id, asset_bytes, asset_type))

    async def wait_for_result(self, task_id: str, timeout: float = 30.0) -> Optional[Dict]:
        """
        Wait for moderation result asynchronously.

        Args:
            task_id: Task identifier
            timeout: Max seconds to wait

        Returns:
            Aggregated moderation result or None if timeout
        """
        fut = self._pending.get(task_id)
        if fut:
            try:
                return await asyncio.wait_for(fut, timeout=timeout)
            except asyncio.TimeoutError:
                return {"error": "timeout", "task_id": task_id}
        return None

    async def shutdown(self):
        """Gracefully shutdown the coordinator."""
        self._closed = True
        self._executor.shutdown(wait=False)

    # -------------------------------------------------
    # Worker Startup
    # -------------------------------------------------

    async def run_workers(self):
        """
        Start batching + async workers in parallel.
        """
        # Pre-load models
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, _load_models)

        await asyncio.gather(
            self._run_batcher(),
            self._run_ocr_worker(),
            self._run_nsfw_worker(),
            self._run_violence_worker(),
            self._run_weapons_worker(),
            self._run_policy_worker(),
        )

    # -------------------------------------------------
    # Batching Loop
    # -------------------------------------------------

    async def _run_batcher(self):
        """Collects tasks and forms batches for workers."""
        while not self._closed:
            try:
                task = await asyncio.wait_for(
                    self._batch_queue.get(),
                    timeout=self.max_wait_ms
                )
            except asyncio.TimeoutError:
                task = None

            async with self._batch_lock:
                if task:
                    task_id, asset, asset_type = task
                    self._buckets["raw"].append((task_id, asset, asset_type))

                # Flush when batch is full or on timeout with pending items
                if len(self._buckets["raw"]) >= self.batch_size:
                    batch = self._buckets["raw"][:self.batch_size]
                    self._buckets["raw"] = self._buckets["raw"][self.batch_size:]
                    await self._schedule_batch_to_workers(batch)
                elif task is None and self._buckets["raw"]:
                    batch = self._buckets["raw"]
                    self._buckets["raw"] = []
                    await self._schedule_batch_to_workers(batch)

    async def _schedule_batch_to_workers(self, batch: List[tuple]):
        """Broadcast batch to all worker pipelines."""
        # Each worker gets a copy of the batch
        self._buckets["ocr_in"].extend(batch)
        self._buckets["nsfw_in"].extend(batch)
        self._buckets["violence_in"].extend(batch)
        self._buckets["weapons_in"].extend(batch)
        self._buckets["policy_in"].extend(batch)

    # -------------------------------------------------
    # Worker Implementations (with real models)
    # -------------------------------------------------

    async def _run_ocr_worker(self):
        """Worker: Extract text from images using PaddleOCR."""
        while not self._closed:
            if not self._buckets["ocr_in"]:
                await asyncio.sleep(0.005)
                continue

            batch = self._buckets["ocr_in"]
            self._buckets["ocr_in"] = []

            for task_id, asset_bytes, asset_type in batch:
                if asset_type == "text":
                    # Text assets don't need OCR
                    self._append_result(task_id, "ocr", {"text": "", "skipped": True})
                    continue

                result = await self._run_ocr(asset_bytes)
                self._append_result(task_id, "ocr", result)

    async def _run_nsfw_worker(self):
        """Worker: Detect NSFW content."""
        while not self._closed:
            if not self._buckets["nsfw_in"]:
                await asyncio.sleep(0.005)
                continue

            batch = self._buckets["nsfw_in"]
            self._buckets["nsfw_in"] = []

            for task_id, asset_bytes, asset_type in batch:
                if asset_type == "text":
                    self._append_result(task_id, "nsfw", {"score": 0.0, "skipped": True})
                    continue

                result = await self._run_nsfw(asset_bytes)
                self._append_result(task_id, "nsfw", result)

    async def _run_violence_worker(self):
        """Worker: Detect violence and blood."""
        while not self._closed:
            if not self._buckets["violence_in"]:
                await asyncio.sleep(0.005)
                continue

            batch = self._buckets["violence_in"]
            self._buckets["violence_in"] = []

            for task_id, asset_bytes, asset_type in batch:
                if asset_type == "text":
                    self._append_result(task_id, "violence", {"score": 0.0, "skipped": True})
                    continue

                result = await self._run_violence(asset_bytes)
                self._append_result(task_id, "violence", result)

    async def _run_weapons_worker(self):
        """Worker: Detect weapons."""
        while not self._closed:
            if not self._buckets["weapons_in"]:
                await asyncio.sleep(0.005)
                continue

            batch = self._buckets["weapons_in"]
            self._buckets["weapons_in"] = []

            for task_id, asset_bytes, asset_type in batch:
                if asset_type == "text":
                    self._append_result(task_id, "weapons", {"score": 0.0, "skipped": True})
                    continue

                result = await self._run_weapons(asset_bytes)
                self._append_result(task_id, "weapons", result)

    async def _run_policy_worker(self):
        """Worker: Apply policy rules and make final decision."""
        while not self._closed:
            if not self._buckets["policy_in"]:
                await asyncio.sleep(0.005)
                continue

            batch = self._buckets["policy_in"]
            self._buckets["policy_in"] = []

            for task_id, asset_bytes, asset_type in batch:
                result = await self._run_policy(task_id)
                self._append_result(task_id, "policy", result)

    # -------------------------------------------------
    # Result Aggregator
    # -------------------------------------------------

    def _append_result(self, task_id: str, key: str, value: Any):
        """Append partial result and complete future when all pipelines done."""
        if task_id not in self._results:
            self._results[task_id] = {"task_id": task_id}

        self._results[task_id][key] = value

        # Check if all 5 pipelines completed
        result = self._results[task_id]
        required_keys = {"ocr", "nsfw", "violence", "weapons", "policy"}

        if required_keys.issubset(result.keys()):
            # All pipelines complete - finalize result
            final_result = self._finalize_result(task_id)

            fut = self._pending.get(task_id)
            if fut and not fut.done():
                fut.set_result(final_result)

            # Cleanup
            del self._results[task_id]
            if task_id in self._pending:
                del self._pending[task_id]

    def _finalize_result(self, task_id: str) -> Dict[str, Any]:
        """Aggregate all pipeline results into final moderation decision."""
        result = self._results.get(task_id, {})

        # Extract scores
        nsfw_score = result.get("nsfw", {}).get("score", 0.0)
        violence_score = result.get("violence", {}).get("violence_score", 0.0)
        blood_score = result.get("violence", {}).get("blood_score", 0.0)
        weapon_score = result.get("weapons", {}).get("weapon_score", 0.0)

        # Get OCR text
        ocr_text = result.get("ocr", {}).get("text", "")

        # Get policy result
        policy = result.get("policy", {})

        # Calculate max risk score
        max_score = max(nsfw_score, violence_score, blood_score, weapon_score)

        # Determine decision
        if max_score >= 0.8 or policy.get("should_block", False):
            decision = "block"
            risk_level = "critical"
        elif max_score >= 0.5 or policy.get("has_violations", False):
            decision = "review"
            risk_level = "high"
        elif max_score >= 0.3:
            decision = "review"
            risk_level = "medium"
        else:
            decision = "approve"
            risk_level = "low"

        # Build flags
        flags = []
        if nsfw_score > 0.5:
            flags.append("nsfw")
        if violence_score > 0.5:
            flags.append("violence")
        if blood_score > 0.5:
            flags.append("blood")
        if weapon_score > 0.3:
            flags.append("weapons")
        flags.extend(policy.get("flags", []))

        return {
            "task_id": task_id,
            "decision": decision,
            "risk_level": risk_level,
            "global_score": 1.0 - max_score,  # Higher = safer
            "category_scores": {
                "nsfw": nsfw_score,
                "violence": violence_score,
                "blood": blood_score,
                "weapons": weapon_score
            },
            "flags": list(set(flags)),
            "ocr_text": ocr_text,
            "policy": policy,
            "pipelines_completed": 5
        }

    # -------------------------------------------------
    # Model Execution (actual implementations)
    # -------------------------------------------------

    async def _run_ocr(self, asset_bytes: bytes) -> Dict[str, Any]:
        """Run OCR on image bytes."""
        models = _load_models()
        ocr = models.get('ocr')

        if not ocr:
            return {"text": "", "error": "OCR not available"}

        temp_path = None
        try:
            # Save bytes to temp file
            loop = asyncio.get_event_loop()
            temp_path = await loop.run_in_executor(
                self._executor,
                _save_bytes_to_temp,
                asset_bytes,
                ".jpg"
            )

            # Run OCR
            result = await loop.run_in_executor(
                self._executor,
                ocr.extract_text,
                temp_path
            )

            return {
                "text": result.get("text", ""),
                "lines": result.get("lines", []),
                "num_lines": result.get("num_lines", 0)
            }
        except Exception as e:
            return {"text": "", "error": str(e)}
        finally:
            if temp_path:
                _cleanup_temp(temp_path)

    async def _run_nsfw(self, asset_bytes: bytes) -> Dict[str, Any]:
        """Run NSFW detection on image bytes."""
        models = _load_models()
        nsfw = models.get('nsfw')

        if not nsfw:
            return {"score": 0.0, "error": "NSFW detector not available"}

        temp_path = None
        try:
            loop = asyncio.get_event_loop()
            temp_path = await loop.run_in_executor(
                self._executor,
                _save_bytes_to_temp,
                asset_bytes,
                ".jpg"
            )

            result = await loop.run_in_executor(
                self._executor,
                nsfw.analyze_image,
                temp_path
            )

            return {
                "score": max(result.get("nudity", 0.0), result.get("sexual_content", 0.0)),
                "nudity": result.get("nudity", 0.0),
                "sexual_content": result.get("sexual_content", 0.0)
            }
        except Exception as e:
            return {"score": 0.0, "error": str(e)}
        finally:
            if temp_path:
                _cleanup_temp(temp_path)

    async def _run_violence(self, asset_bytes: bytes) -> Dict[str, Any]:
        """Run violence and blood detection on image bytes."""
        models = _load_models()
        violence = models.get('violence')
        blood = models.get('blood')

        temp_path = None
        try:
            loop = asyncio.get_event_loop()
            temp_path = await loop.run_in_executor(
                self._executor,
                _save_bytes_to_temp,
                asset_bytes,
                ".jpg"
            )

            violence_score = 0.0
            blood_score = 0.0

            if violence:
                v_result = await loop.run_in_executor(
                    self._executor,
                    violence.detect,
                    temp_path
                )
                violence_score = v_result.get("violence_score", 0.0)

            if blood:
                b_result = await loop.run_in_executor(
                    self._executor,
                    blood.detect,
                    temp_path
                )
                blood_score = b_result.get("blood_score", 0.0)

            return {
                "violence_score": violence_score,
                "blood_score": blood_score
            }
        except Exception as e:
            return {"violence_score": 0.0, "blood_score": 0.0, "error": str(e)}
        finally:
            if temp_path:
                _cleanup_temp(temp_path)

    async def _run_weapons(self, asset_bytes: bytes) -> Dict[str, Any]:
        """Run weapon detection on image bytes."""
        models = _load_models()
        weapon = models.get('weapon')

        if not weapon:
            return {"weapon_score": 0.0, "error": "Weapon detector not available"}

        temp_path = None
        try:
            loop = asyncio.get_event_loop()
            temp_path = await loop.run_in_executor(
                self._executor,
                _save_bytes_to_temp,
                asset_bytes,
                ".jpg"
            )

            result = await loop.run_in_executor(
                self._executor,
                weapon.detect,
                temp_path
            )

            return {
                "weapon_score": result.get("weapon_score", 0.0),
                "weapon_detected": result.get("weapon_detected", False),
                "weapon_types": result.get("weapon_types", [])
            }
        except Exception as e:
            return {"weapon_score": 0.0, "error": str(e)}
        finally:
            if temp_path:
                _cleanup_temp(temp_path)

    async def _run_policy(self, task_id: str) -> Dict[str, Any]:
        """Apply policy rules based on accumulated results."""
        models = _load_models()
        text_rules = models.get('text_rules')
        detoxify = models.get('detoxify')

        result = self._results.get(task_id, {})
        ocr_text = result.get("ocr", {}).get("text", "")

        policy_result = {
            "has_violations": False,
            "should_block": False,
            "flags": [],
            "reasons": []
        }

        # Check text rules
        if text_rules and ocr_text:
            try:
                loop = asyncio.get_event_loop()
                rules_result = await loop.run_in_executor(
                    self._executor,
                    text_rules.check,
                    ocr_text
                )

                if rules_result.get("has_violations"):
                    policy_result["has_violations"] = True
                    policy_result["flags"].extend(rules_result.get("flags", []))
                    policy_result["reasons"].extend(rules_result.get("reasons", []))

                if rules_result.get("should_block"):
                    policy_result["should_block"] = True

            except Exception as e:
                policy_result["error"] = str(e)

        # Check toxicity
        if detoxify and ocr_text:
            try:
                loop = asyncio.get_event_loop()
                toxicity = await loop.run_in_executor(
                    self._executor,
                    detoxify.analyze,
                    ocr_text
                )

                if toxicity.get("toxicity", 0.0) > 0.5:
                    policy_result["has_violations"] = True
                    policy_result["flags"].append("toxic_text")

                policy_result["toxicity_scores"] = toxicity

            except Exception as e:
                pass

        return policy_result


# Convenience function to create and run coordinator
async def run_batch_moderation(
    assets: List[tuple],  # List of (task_id, bytes, type)
    batch_size: int = 8
) -> List[Dict]:
    """
    Convenience function to moderate a batch of assets.

    Args:
        assets: List of (task_id, asset_bytes, asset_type) tuples
        batch_size: Batch size for processing

    Returns:
        List of moderation results
    """
    coordinator = BatchCoordinator(batch_size=batch_size)

    # Start workers in background
    worker_task = asyncio.create_task(coordinator.run_workers())

    # Schedule all assets
    for task_id, asset_bytes, asset_type in assets:
        await coordinator.schedule(task_id, asset_bytes, asset_type)

    # Wait for all results
    results = []
    for task_id, _, _ in assets:
        result = await coordinator.wait_for_result(task_id)
        results.append(result)

    # Shutdown
    await coordinator.shutdown()
    worker_task.cancel()

    return results


