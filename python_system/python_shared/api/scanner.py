"""
scanner.py - Content Scanner API
Scans ads for policy violations using moderation service
Converted from PHP to Python
"""

from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import httpx
import json
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()

# Configuration
MODERATION_SERVICE_URL = "http://localhost:8002"
SCAN_RESULTS_PATH = Path(__file__).parent.parent / "data" / "scan_results"
SCAN_RESULTS_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/scanner/scan")
async def scan_ads(
    mode: str = Query("incremental", description="Scan mode: full, incremental"),
    db: Session = Depends(get_db)
):
    """Scan ads for policy violations"""
    try:
        start_time = time.time()
        results = {
            "mode": mode,
            "scanned": 0,
            "clean": 0,
            "flagged": 0,
            "errors": 0,
            "flagged_ads": []
        }

        # Get ads to scan
        query = db.query(Ad)
        if mode == "incremental":
            # Only scan ads not scanned in last 24 hours
            # For now, scan all active ads
            query = query.filter(Ad.status == "active")

        ads = query.all()

        for ad in ads:
            results["scanned"] += 1

            try:
                # Prepare content for moderation
                content = {
                    "ad_id": ad.ad_id,
                    "title": ad.title or "",
                    "description": ad.description or "",
                    "category": ad.category_slug
                }

                # Try to call moderation service
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.post(
                            f"{MODERATION_SERVICE_URL}/moderate/text",
                            json=content
                        )
                        if response.status_code == 200:
                            moderation_result = response.json()
                            decision = moderation_result.get("decision", "approve")

                            if decision in ["block", "review"]:
                                results["flagged"] += 1
                                results["flagged_ads"].append({
                                    "ad_id": ad.ad_id,
                                    "title": ad.title,
                                    "decision": decision,
                                    "severity": moderation_result.get("severity", "medium"),
                                    "reasons": moderation_result.get("reasons", [])
                                })
                            else:
                                results["clean"] += 1
                        else:
                            # Fallback to simple text scan
                            flagged, reasons = simple_text_scan(content)
                            if flagged:
                                results["flagged"] += 1
                                results["flagged_ads"].append({
                                    "ad_id": ad.ad_id,
                                    "title": ad.title,
                                    "decision": "review",
                                    "severity": "low",
                                    "reasons": reasons
                                })
                            else:
                                results["clean"] += 1
                except Exception:
                    # Use fallback scanner
                    flagged, reasons = simple_text_scan(content)
                    if flagged:
                        results["flagged"] += 1
                        results["flagged_ads"].append({
                            "ad_id": ad.ad_id,
                            "title": ad.title,
                            "decision": "review",
                            "severity": "low",
                            "reasons": reasons
                        })
                    else:
                        results["clean"] += 1

            except Exception as e:
                results["errors"] += 1

        # Calculate duration
        duration = round((time.time() - start_time) * 1000, 2)
        results["duration_ms"] = duration
        results["ads_per_second"] = round(results["scanned"] / max(duration / 1000, 0.001), 2)

        # Save scan results
        scan_file = SCAN_RESULTS_PATH / f"scan_{int(time.time())}.json"
        with open(scan_file, "w") as f:
            json.dump(results, f, indent=2)

        return {
            "success": True,
            **results
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


def simple_text_scan(content: dict) -> tuple:
    """Simple keyword-based content scanning"""
    flagged = False
    reasons = []

    # Banned words
    banned_words = [
        "weapon", "gun", "drugs", "cocaine", "marijuana", "kill", "murder",
        "scam", "fraud", "illegal", "counterfeit", "fake", "stolen",
        "xxx", "porn", "nude", "escort", "prostitut"
    ]

    text = f"{content.get('title', '')} {content.get('description', '')}".lower()

    for word in banned_words:
        if word in text:
            flagged = True
            reasons.append(f"Contains banned word: {word}")

    return flagged, reasons


@router.get("/scanner/results")
async def get_scan_results(limit: int = Query(10, ge=1, le=100)):
    """Get recent scan results"""
    try:
        results = []

        # Get recent scan files
        scan_files = sorted(SCAN_RESULTS_PATH.glob("scan_*.json"), reverse=True)[:limit]

        for file_path in scan_files:
            with open(file_path, "r") as f:
                result = json.load(f)
                result["scan_file"] = file_path.stem
                results.append(result)

        return {
            "success": True,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/scanner/status")
async def scanner_status():
    """Get scanner service status"""
    try:
        # Check moderation service
        moderation_available = False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{MODERATION_SERVICE_URL}/health")
                moderation_available = response.status_code == 200
        except Exception:
            pass

        # Get last scan info
        scan_files = sorted(SCAN_RESULTS_PATH.glob("scan_*.json"), reverse=True)
        last_scan = None
        if scan_files:
            with open(scan_files[0], "r") as f:
                last_scan = json.load(f)

        return {
            "success": True,
            "status": "ready",
            "moderation_service": "available" if moderation_available else "unavailable",
            "last_scan": last_scan
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

