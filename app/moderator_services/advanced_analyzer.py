#!/usr/bin/env python3

"""
Multimodal Ad Moderation Pipeline (extended)
-------------------------------------------

New features:
- Image captioning for scene/object description
- Moderation output includes human-readable interpretation
- Video-ready modular scoring
"""

import os
import sys
import tempfile
from pathlib import Path
from PIL import Image

# Add path for model_registry
sys.path.insert(0, str(Path(__file__).parent))
from model_registry import ensure_models

# Ensure models are available
REQUIRED_MODELS = ['transformers', 'torch', 'PIL']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ AdvancedAnalyzer: Some models not available")

import torch
from transformers import (
    pipeline,
    CLIPProcessor,
    CLIPModel,
    BlipProcessor,
    BlipForConditionalGeneration
)
import easyocr

# ================================
# DEVICE CONFIG
# ================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
pipe_device = 0 if torch.cuda.is_available() else -1

print("Using device:", device)

# ================================
# LOAD MODELS
# ================================

print("Loading models...")

ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

text_classifier = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    device=pipe_device
)

nsfw_model = pipeline(
    "image-classification",
    model="Falconsai/nsfw_image_detection",
    device=pipe_device
)

clip_model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
).to(device)
clip_proc = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)

# caption model
print("Loading caption model...")
caption_model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
).to(device)

caption_proc = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

# YOLO optional
try:
    import ultralytics
    from ultralytics import YOLO
    yolo = YOLO("yolov8n.pt")
except:
    print("⚠ YOLO unavailable")
    yolo = None

print("All models ready.\n")


# ==========================================================
# HELPERS
# ==========================================================

def extract_text(image):
    """Extract text via OCR safely."""
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as f:
            tmp_file = f.name
            image.save(tmp_file)

        result = ocr_reader.readtext(tmp_file)
        return " ".join(r[1] for r in result).strip() if result else ""

    except Exception as e:
        print("OCR Error:", e)
        return ""

    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)


def describe_image(image):
    """Generate scene/object caption."""
    try:
        inputs = caption_proc(
            image,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            out = caption_model.generate(
                **inputs,
                max_length=50,
                num_beams=3
            )
        text = caption_proc.decode(
            out[0],
            skip_special_tokens=True
        )
        return text.strip()

    except Exception as e:
        print("Caption error:", e)
        return ""


def score_text_toxicity(text):
    if not text:
        return 0.0
    pred = text_classifier(text[:512])[0]
    if pred["label"].lower() in ["toxic", "severe_toxic", "threat", "insult", "hate"]:
        return pred["score"]
    return 0.0


def score_nudity(image):
    preds = nsfw_model(image)
    return max((p["score"] for p in preds if p["label"] == "nsfw"), default=0.0)


def detect_objects_yolo(image):
    if yolo is None:
        return 0.0

    r = yolo(image)
    names = r[0].names
    cls = r[0].boxes.cls
    objs = [names[int(c)] for c in cls]

    weapon_classes = {
        "knife", "scissors",
        "gun", "pistol", "rifle", "shotgun"
    }
    count = sum(1 for o in objs if o.lower() in weapon_classes)
    return min(count * 0.5, 1.0)


def detect_weapons_clip(image):
    try:
        harmful = [
            "a gun","a pistol","a rifle",
            "a firearm","ammunition",
            "a handgun","machine gun",
        ]
        safe = [
            "stop gun violence sign",
            "peaceful protest",
            "product photo",
        ]
        prompts = harmful + safe

        inputs = clip_proc(
            text=prompts,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(device)

        with torch.no_grad():
            logits = clip_model(**inputs).logits_per_image[0]
            probs = logits.softmax(dim=0)

        harm = probs[:len(harmful)].sum().item()
        safe_p = probs[len(harmful):].sum().item()
        max_harm = probs[:len(harmful)].max().item()

        if harm > safe_p and max_harm > 0.15:
            return min((harm/(harm+safe_p)) * max_harm * 3, 1.0)

        return 0.0

    except Exception:
        return 0.0


def detect_self_harm(image):
    harmful = [
        "a person about to hang themselves",
        "self harm",
        "a noose",
        "suicide imagery",
        "a person cutting themselves"
    ]
    safe = [
        "rope for climbing",
        "product photo",
        "smiling person"
    ]

    prompts = harmful + safe
    try:
        inputs = clip_proc(text=prompts, images=image,
                           return_tensors="pt", padding=True).to(device)

        with torch.no_grad():
            logits = clip_model(**inputs).logits_per_image[0]
            probs = logits.softmax(dim=0)

        harm = probs[:len(harmful)].sum().item()
        safe_p = probs[len(harmful):].sum().item()
        max_harm = probs[:len(harmful)].max().item()

        if harm > safe_p and max_harm > 0.1:
            return min((harm/(harm+safe_p)) * max_harm * 4, 1.0)

        return 0.0

    except:
        return 0.0


def classify_intent(image, text):
    if not text:
        return 0.0
    harm = ["promote violence", "sell weapons"]
    safe = ["stop violence", "condemn hate"]

    t1 = clip_proc(text=harm, images=image,
                   return_tensors="pt", padding=True).to(device)
    t2 = clip_proc(text=safe, images=image,
                   return_tensors="pt", padding=True).to(device)

    with torch.no_grad():
        h = clip_model(**t1).logits_per_image.mean().item()
        s = clip_model(**t2).logits_per_image.mean().item()

    return max(h - s, 0)


# =====================================================
# FINAL DECISION
# =====================================================

def final_decision(text_score, weap, nudity, intent, self_harm, text):

    lw = text.lower()
    weapon_terms = ["gun", "rifle", "weapon", "firearm", "pistol"]
    sell_terms = ["sell", "buy", "price", "discount"]

    if any(w in lw for w in weapon_terms) and any(
        s in lw for s in sell_terms
    ):
        weap = max(weap, 0.9)

    severity = (
        text_score * 0.25 +
        weap * 0.35 +
        nudity * 0.15 +
        self_harm * 0.15 +
        intent * 0.10
    )

    if any([
        text_score >= 0.9,
        weap >= 0.7,
        nudity >= 0.8,
        self_harm >= 0.5
    ]):
        return "BLOCK", max(severity, 0.8)

    if severity >= 0.45:
        return "BLOCK", severity

    if severity >= 0.20:
        return "REVIEW", severity

    return "APPROVE", severity


# =====================================================
# MAIN PIPELINE
# =====================================================

def moderate(image):
    image = image.convert("RGB")

    text = extract_text(image)
    caption = describe_image(image)

    t = score_text_toxicity(text)
    w1 = detect_weapons_clip(image)
    w2 = detect_objects_yolo(image)
    weapon = max(w1, w2)

    nudity = score_nudity(image)
    self_harm = detect_self_harm(image)
    intent = classify_intent(image, text)

    decision, score = final_decision(
        t, weapon, nudity, intent, self_harm, text
    )

    return {
        "decision": decision,
        "severity": round(score, 3),
        "description": caption,
        "text_detected": text,
        "reasons": {
            "text_toxic": t,
            "weapon": weapon,
            "weapon_clip": w1,
            "weapon_yolo": w2,
            "nudity": nudity,
            "self_harm": self_harm,
            "intent": intent
        }
    }


# =====================================================
# TEST BATCH SCAN
# =====================================================

if __name__ == "__main__":
    SAMPLE_DIR = Path("./sample_images")
    exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

    if not SAMPLE_DIR.exists():
        print(f"❌ Directory not found: {SAMPLE_DIR}")
        exit(1)

    imgs = sorted(
        f for f in SAMPLE_DIR.iterdir() if f.suffix.lower() in exts
    )

    print()
    print("=" * 90)
    print("  ADVANCED IMAGE ANALYSIS WITH AI CAPTIONING")
    print("  Analyzing", len(imgs), "images")
    print("=" * 90)
    print()

    results = {"APPROVE": [], "REVIEW": [], "BLOCK": []}

    for idx, img_path in enumerate(imgs, 1):
        print(f"[{idx}/{len(imgs)}] 📸 {img_path.name}")
        print("-" * 80)

        try:
            im = Image.open(img_path)
            result = moderate(im)

            # Show AI description
            print(f"   🤖 AI DESCRIPTION: \"{result['description']}\"")
            print()

            # Show extracted text
            if result['text_detected']:
                text_preview = result['text_detected'][:80]
                print(f"   📝 TEXT DETECTED: \"{text_preview}{'...' if len(result['text_detected']) > 80 else ''}\"")
            else:
                print(f"   📝 TEXT DETECTED: (none)")
            print()

            # Show scores
            print(f"   📊 DETECTION SCORES:")
            print(f"      • Text Toxicity:  {result['reasons']['text_toxic']:.2f}")
            print(f"      • Weapon:         {result['reasons']['weapon']:.2f} (CLIP: {result['reasons']['weapon_clip']:.2f}, YOLO: {result['reasons']['weapon_yolo']:.2f})")
            print(f"      • Nudity:         {result['reasons']['nudity']:.2f}")
            print(f"      • Self-Harm:      {result['reasons']['self_harm']:.2f}")
            print(f"      • Harmful Intent: {result['reasons']['intent']:.2f}")
            print()

            # Decision
            emoji = {"APPROVE": "✅", "REVIEW": "⚠️", "BLOCK": "🚫"}[result['decision']]
            print(f"   {emoji} DECISION: {result['decision']} (severity: {result['severity']})")

            results[result['decision']].append(img_path.name)

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    # Summary
    print("=" * 90)
    print("  FINAL SUMMARY")
    print("=" * 90)
    print()
    print(f"   ✅ APPROVED: {len(results['APPROVE'])} images")
    print(f"   ⚠️  REVIEW:   {len(results['REVIEW'])} images")
    print(f"   🚫 BLOCKED:  {len(results['BLOCK'])} images")
    print()

    if results["BLOCK"]:
        print("   🚫 BLOCKED:")
        for name in results["BLOCK"]:
            print(f"      • {name}")
        print()

    print("=" * 90)
