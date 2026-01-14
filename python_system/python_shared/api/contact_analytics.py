"""
contact_analytics.py - Contact Method Analytics API
Comprehensive analytics for SMS, Call, Email, WhatsApp
Converted from PHP to Python
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

router = APIRouter()

ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"


def detect_age_group(user_agent: str) -> str:
    """Simple heuristic to detect age group from user agent"""
    ua_lower = user_agent.lower()

    youth_patterns = ['tiktok', 'snapchat', 'instagram', 'mobile', 'android']
    middle_age_patterns = ['facebook', 'linkedin', 'chrome', 'safari']
    elderly_patterns = ['desktop', 'windows', 'msie', 'edge']

    for pattern in youth_patterns:
        if pattern in ua_lower:
            return 'youth'
    for pattern in middle_age_patterns:
        if pattern in ua_lower:
            return 'middle_age'
    for pattern in elderly_patterns:
        if pattern in ua_lower:
            return 'elderly'

    return 'unknown'


@router.get("/contact_analytics")
async def contact_analytics(
    ad_id: str = Query(None),
    company: str = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Get contact method analytics"""
    try:
        # Initialize contact methods
        contact_methods = {
            "sms": {"count": 0, "trend": [], "hourly": [0] * 24},
            "call": {"count": 0, "trend": [], "hourly": [0] * 24},
            "email": {"count": 0, "trend": [], "hourly": [0] * 24},
            "whatsapp": {"count": 0, "trend": [], "hourly": [0] * 24}
        }

        demographics = {
            "youth": 0,
            "middle_age": 0,
            "elderly": 0,
            "unknown": 0
        }

        # Calculate cutoff timestamp
        cutoff = int(time.time()) - (days * 86400)

        # Initialize daily data
        daily_data = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_data[date] = {method: 0 for method in contact_methods.keys()}

        if not ANALYTICS_PATH.exists():
            return {
                "success": True,
                "contact_methods": contact_methods,
                "demographics": demographics,
                "ai_insights": []
            }

        # Process analytics files
        files_to_process = []

        if ad_id:
            # Specific ad
            analytics_file = ANALYTICS_PATH / f"{ad_id}.json"
            if analytics_file.exists():
                files_to_process.append(analytics_file)
        else:
            # All files
            files_to_process = list(ANALYTICS_PATH.glob("*.json"))

        for analytics_file in files_to_process:
            try:
                with open(analytics_file, "r") as f:
                    analytics = json.load(f)

                events = analytics.get("events", [])

                for event in events:
                    event_type = event.get("type", "")
                    timestamp = event.get("timestamp", 0)

                    # Only include events within the time range
                    if timestamp < cutoff:
                        continue

                    # Count contact methods
                    if event_type in contact_methods:
                        contact_methods[event_type]["count"] += 1

                        # Hourly distribution
                        hour = datetime.fromtimestamp(timestamp).hour
                        contact_methods[event_type]["hourly"][hour] += 1

                        # Daily trend
                        date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                        if date in daily_data:
                            daily_data[date][event_type] += 1

                        # Demographics
                        user_agent = event.get("user_agent", "")
                        age_group = detect_age_group(user_agent)
                        demographics[age_group] += 1

            except Exception:
                continue

        # Build trend arrays
        for method in contact_methods.keys():
            for date in sorted(daily_data.keys()):
                contact_methods[method]["trend"].append({
                    "date": date,
                    "count": daily_data[date][method]
                })

        # Determine best method
        best_method = max(contact_methods.keys(), key=lambda m: contact_methods[m]["count"])

        # Generate AI insights
        ai_insights = generate_contact_insights(contact_methods, demographics)

        return {
            "success": True,
            "contact_methods": contact_methods,
            "demographics": demographics,
            "best_method": best_method,
            "ai_insights": ai_insights,
            "days_analyzed": days
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


def generate_contact_insights(contact_methods: dict, demographics: dict) -> list:
    """Generate AI-powered insights from contact analytics"""
    insights = []

    # Total contacts
    total_contacts = sum(m["count"] for m in contact_methods.values())

    if total_contacts == 0:
        return ["No contact data available yet. Start tracking to get insights."]

    # Best performing method
    best_method = max(contact_methods.keys(), key=lambda m: contact_methods[m]["count"])
    best_count = contact_methods[best_method]["count"]
    best_percentage = round((best_count / total_contacts) * 100, 1)

    insights.append(f"{best_method.upper()} is your best performing channel with {best_percentage}% of all contacts.")

    # WhatsApp insight
    whatsapp_count = contact_methods["whatsapp"]["count"]
    if whatsapp_count > 0:
        wa_percentage = round((whatsapp_count / total_contacts) * 100, 1)
        if wa_percentage > 40:
            insights.append(f"WhatsApp dominates with {wa_percentage}%. Consider adding quick reply templates.")
        elif wa_percentage < 10:
            insights.append("WhatsApp usage is low. Make your WhatsApp button more prominent.")

    # Demographics insight
    total_demo = sum(demographics.values())
    if total_demo > 0:
        dominant_group = max(demographics.keys(), key=lambda g: demographics[g])
        demo_percentage = round((demographics[dominant_group] / total_demo) * 100, 1)

        if dominant_group == "youth":
            insights.append(f"Your ads attract mostly younger users ({demo_percentage}%). Use casual, trendy language.")
        elif dominant_group == "middle_age":
            insights.append(f"Middle-aged users engage most ({demo_percentage}%). Focus on value and reliability.")
        elif dominant_group == "elderly":
            insights.append(f"Older users prefer your ads ({demo_percentage}%). Keep messaging clear and simple.")

    # Time-based insight
    for method, data in contact_methods.items():
        peak_hour = data["hourly"].index(max(data["hourly"]))
        if max(data["hourly"]) > 0:
            insights.append(f"Peak {method} activity is around {peak_hour}:00. Schedule promotions accordingly.")
            break

    return insights[:5]  # Return top 5 insights

