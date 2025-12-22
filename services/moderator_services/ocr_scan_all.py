#!/usr/bin/env python3

"""
Multimodal Ad Moderation Pipeline
---------------------------------

Models used:
- OCR: EasyOCR
- Toxic text: Toxic-BERT
- NSFW classifier: Falcon NSFW
- Visual object detector: YOLOv5
- CLIP visual-text intent alignment

Moderation signals:
- violence / weapons
- nudity
- hate speech
- ad context consistency
- selling weapons detection

Final decisions:
APPROVE | REVIEW | BLOCK
"""

import sys
from pathlib import Path
import tempfile
from PIL import Image
import torch
from ultralytics import YOLO
from transformers import (
    pipeline,
    CLIPProcessor,
    CLIPModel
)

import easyocr

# Import model registry
from model_registry import ensure_models, get_model_path

# Ensure required models are available
REQUIRED_MODELS = ['yolov8n', 'ultralytics', 'transformers', 'torch', 'PIL']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ OCR Scanner: Some models not available, continuing with available models...")


# =====================================================
# LOAD MODELS
# =====================================================

print("Loading models...")

print("Loading EasyOCR...")
ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

print("Loading Toxic‑BERT...")
text_classifier = pipeline("text-classification", model="unitary/toxic-bert")

print("Loading NSFW classifier...")
nsfw_model = pipeline("image-classification", model="Falconsai/nsfw_image_detection")

print("Loading CLIP...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

print("Loading YOLOv5...")
try:
    model_path = get_model_path('yolov8n')
    if model_path:
        yolo = YOLO(str(model_path))
    else:
        yolo = YOLO("yolov8n.pt")
except:
    print("YOLO unavailable")
    yolo = None

print("All models ready!")
print()


# =====================================================
# FUNCTIONS
# =====================================================

def extract_text(image):
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            image.save(f.name)
            result = ocr_reader.readtext(f.name)
        if result:
            return " ".join([r[1] for r in result]).strip()
        return ""
    except Exception as e:
        print("OCR ERROR:", e)
        return ""


def score_text_toxicity(text):
    if not text or len(text) < 3:
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
    try:
        r = yolo(image)
        df = r.pandas().xyxy[0]
        objs = df["name"].astype(str).tolist()
        # YOLO tiny weapon classes
        weapon_classes = {"knife", "scissors"}
        count = sum(1 for o in objs if o.lower() in weapon_classes)
        return min(count * 0.5, 1.0)
    except:
        return 0.0


def detect_weapons_clip(image):
    try:
        harmful_prompts = [
            "a gun",
            "a rifle",
            "a pistol",
            "a machine gun",
            "a handgun",
            "a firearm",
            "ammunition"
        ]
        safe_prompts = [
            "people protesting peacefully",
            "stop gun violence sign",
            "a photo of food",
            "freedom banner",
            "magazine text"
        ]
        prompts = harmful_prompts + safe_prompts
        inputs = clip_proc(text=prompts, images=image,
                           return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = clip_model(**inputs).logits_per_image[0]
            probs = logits.softmax(dim=0)

        harm = probs[:len(harmful_prompts)].sum().item()
        safe = probs[len(harmful_prompts):].sum().item()

        max_harm = probs[:len(harmful_prompts)].max().item()

        if harm > safe and max_harm > 0.15:
            return min((harm / (harm + safe)) * max_harm * 3, 1.0)
        return 0.0
    except:
        return 0.0


def detect_self_harm(image):
    """Detect self-harm/suicide imagery like noose, hanging, cutting"""
    try:
        # Very specific self-harm prompts
        harmful_prompts = [
            "a noose hanging from ceiling",
            "a hangman's noose made of rope",
            "person with noose around neck",
            "suicide by hanging scene",
            "self harm cutting wrists",
            "person about to commit suicide",
        ]

        # More safe prompts to reduce false positives
        safe_prompts = [
            "a peaceful protest demonstration",
            "people marching with signs",
            "a happy family photo",
            "food on a table",
            "a building or house",
            "people smiling and celebrating",
            "climbing rope sports",
            "decorative rope on a boat",
            "a gun or firearm photo",  # Different category
            "a fight or assault",  # Different category
            "blood from an injury",  # Different category
            "real estate advertisement",
            "product advertisement photo",
        ]

        prompts = harmful_prompts + safe_prompts
        inputs = clip_proc(text=prompts, images=image,
                           return_tensors="pt", padding=True)

        with torch.no_grad():
            logits = clip_model(**inputs).logits_per_image[0]
            probs = logits.softmax(dim=0)

        harm = probs[:len(harmful_prompts)].sum().item()
        safe = probs[len(harmful_prompts):].sum().item()
        max_harm = probs[:len(harmful_prompts)].max().item()

        # Need CLEAR dominance of self-harm prompts
        # Must be: harm > safe AND max single prompt > 20%
        if harm > safe and max_harm > 0.20:
            return min((harm / (harm + safe)) * max_harm * 3, 1.0)
        return 0.0
    except Exception as e:
        print(f"Self-harm detection error: {e}")
        return 0.0


def classify_intent(image, text):
    if not text:
        return 0.0

    harm = ["promote violence", "support hate", "selling weapons"]
    benign = ["stop violence", "condemn hate", "anti violence message"]

    t1 = clip_proc(text=harm, images=image, return_tensors="pt", padding=True)
    t2 = clip_proc(text=benign, images=image, return_tensors="pt", padding=True)

    with torch.no_grad():
        s_h = clip_model(**t1).logits_per_image.mean().item()
        s_s = clip_model(**t2).logits_per_image.mean().item()

    return max(s_h - s_s, 0)


# FINAL DECISION -------------------------------------------------

def final_decision(text_score, weap, nudity, intent, self_harm, text):

    # explicit weapon sales in text
    lw = text.lower()

    weapon_terms = ["gun", "rifle", "weapon", "firearm", "pistol"]
    sell_terms = ["sell", "buy", "price", "discount"]

    selling_weapon = any(w in lw for w in weapon_terms) and any(
        s in lw for s in sell_terms
    )

    if selling_weapon:
        weap = max(weap, 0.9)

    # Check for anti-violence messages (should be APPROVED)
    anti_violence_terms = ["stop", "end", "no more", "against", "ban", "prevent"]
    violence_terms = ["killing", "killings", "violence", "war", "murder", "death"]

    is_anti_violence = False
    if text:
        for anti in anti_violence_terms:
            if anti in lw:
                for viol in violence_terms:
                    if viol in lw:
                        # Check if anti-violence word comes BEFORE violence word
                        if lw.find(anti) < lw.find(viol):
                            is_anti_violence = True
                            break

    # If it's an anti-violence message, reduce severity
    if is_anti_violence:
        text_score = min(text_score, 0.1)
        self_harm = min(self_harm, 0.1)
        intent = 0.0

    severity = (
        text_score * 0.30 +
        weap * 0.30 +
        nudity * 0.15 +
        self_harm * 0.15 +  # Self-harm detection
        intent * 0.10
    )

    # Direct blocks for high individual scores (but not for anti-violence)
    if not is_anti_violence:
        if text_score >= 0.9:
            return "BLOCK", max(severity, 0.9)

        if weap >= 0.7:
            return "BLOCK", max(severity, 0.7)

        if nudity >= 0.8:
            return "BLOCK", max(severity, 0.8)

        if self_harm >= 0.5:  # Self-harm imagery = immediate block
            return "BLOCK", max(severity, 0.8)

    if severity >= 0.45:
        return "BLOCK", severity

    if severity >= 0.2:
        return "REVIEW", severity

    return "APPROVE", severity


# MAIN -----------------------------------------------------------

def moderate(image):
    image = image.convert("RGB")

    text = extract_text(image)

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
        "severity": score,
        "text": text,
        "scores": {
            "text_toxic": t,
            "weapon": weapon,
            "weapon_clip": w1,
            "weapon_yolo": w2,
            "nudity": nudity,
            "self_harm": self_harm,
            "intent": intent
        }
    }


# OPTIONAL BATCH SCAN ---------------------------------------------

def describe_image(image):
    """Use CLIP to generate a description of what's in the image"""

    # Scene descriptions
    scene_prompts = [
        "a photo of a gun or firearm",
        "a photo of a rifle or machine gun",
        "a photo of a pistol with ammunition",
        "a photo of a noose or hanging rope",
        "a photo of a person in distress",
        "a photo of a protest or demonstration",
        "a photo of people holding signs",
        "a photo of a real estate advertisement",
        "a photo of a house for sale",
        "a photo of food or restaurant",
        "a photo of a product advertisement",
        "a photo of a social media post",
        "a photo of a tweet or text message",
        "a photo of violence or fighting",
        "a photo of blood or injury",
        "a photo of a knife or blade",
        "a photo of nudity or explicit content",
        "a photo of a person smiling",
        "a photo of nature or landscape",
        "a photo of a vehicle or car",
        "a photo of text or writing",
        "a photo of an assault or attack",
    ]

    inputs = clip_proc(text=scene_prompts, images=image, return_tensors="pt", padding=True)

    with torch.no_grad():
        logits = clip_model(**inputs).logits_per_image[0]
        probs = logits.softmax(dim=0)

    # Get top 3 matches
    top_indices = probs.argsort(descending=True)[:3]
    descriptions = []
    for idx in top_indices:
        prob = probs[idx].item()
        if prob > 0.05:  # Only include if >5% confidence
            desc = scene_prompts[idx].replace("a photo of ", "").capitalize()
            descriptions.append(f"{desc} ({prob*100:.1f}%)")

    return descriptions


def get_risk_explanation(scores, text):
    """Generate human-readable explanation of why content was flagged"""
    explanations = []

    if scores["text_toxic"] > 0.5:
        explanations.append(f"⚠️ Toxic text detected ({scores['text_toxic']*100:.0f}% confidence)")

    if scores["weapon"] > 0.5:
        explanations.append(f"🔫 Weapon/firearm detected ({scores['weapon']*100:.0f}% confidence)")

    if scores["self_harm"] > 0.3:
        explanations.append(f"⛔ Self-harm imagery detected ({scores['self_harm']*100:.0f}% confidence)")

    if scores["nudity"] > 0.5:
        explanations.append(f"🔞 NSFW/nudity detected ({scores['nudity']*100:.0f}% confidence)")

    if scores["intent"] > 0.3:
        explanations.append(f"❗ Harmful intent detected ({scores['intent']*100:.0f}%)")

    # Check for weapon sale in text
    if text:
        text_lower = text.lower()
        weapon_words = ['gun', 'rifle', 'pistol', 'weapon', 'ammunition', 'firearm']
        sale_words = ['sale', 'sell', 'buy', 'price']
        if any(w in text_lower for w in weapon_words) and any(s in text_lower for s in sale_words):
            explanations.append("🚫 Weapon sale advertisement detected in text")

    if not explanations:
        explanations.append("✅ No concerning content detected")

    return explanations


if __name__ == "__main__":
    SAMPLE_DIR = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/moderator_services/sample_images")
    exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

    imgs = sorted(
        f for f in SAMPLE_DIR.iterdir() if f.suffix.lower() in exts
    )

    print()
    print("=" * 100)
    print("  ADVANCED MULTIMODAL IMAGE ANALYSIS")
    print("  Analyzing", len(imgs), "images with detailed descriptions")
    print("=" * 100)
    print()

    results_summary = {"APPROVE": [], "REVIEW": [], "BLOCK": []}

    for idx, img_path in enumerate(imgs, 1):
        print(f"[{idx}/{len(imgs)}] 📸 {img_path.name}")
        print("-" * 80)

        try:
            im = Image.open(img_path)

            # Get image description
            descriptions = describe_image(im)

            # Run moderation
            r = moderate(im)

            # Get risk explanation
            explanations = get_risk_explanation(r["scores"], r["text"])

            # Display results
            print(f"   🖼️  WHAT THE MODEL SEES:")
            for desc in descriptions:
                print(f"      • {desc}")

            print()
            print(f"   📝 TEXT EXTRACTED: \"{r['text'][:80]}{'...' if len(r['text']) > 80 else ''}\"" if r['text'] else "   📝 TEXT EXTRACTED: (none)")

            print()
            print(f"   📊 DETECTION SCORES:")
            print(f"      • Text Toxicity:  {r['scores']['text_toxic']:.2f}")
            print(f"      • Weapon:         {r['scores']['weapon']:.2f}")
            print(f"      • Nudity:         {r['scores']['nudity']:.2f}")
            print(f"      • Self-Harm:      {r['scores']['self_harm']:.2f}")
            print(f"      • Harmful Intent: {r['scores']['intent']:.2f}")

            print()
            print(f"   🔍 RISK ANALYSIS:")
            for exp in explanations:
                print(f"      {exp}")

            print()
            emoji = {"APPROVE": "✅", "REVIEW": "⚠️", "BLOCK": "🚫"}[r["decision"]]
            print(f"   {emoji} DECISION: {r['decision']} (severity: {r['severity']:.2f})")

            results_summary[r["decision"]].append(img_path.name)

        except Exception as e:
            print(f"   ❌ Error processing: {e}")

        print()

    # Final Summary
    print("=" * 100)
    print("  FINAL SUMMARY")
    print("=" * 100)
    print()
    print(f"   ✅ APPROVED: {len(results_summary['APPROVE'])} images")
    print(f"   ⚠️  REVIEW:   {len(results_summary['REVIEW'])} images")
    print(f"   🚫 BLOCKED:  {len(results_summary['BLOCK'])} images")
    print()

    if results_summary["BLOCK"]:
        print("   🚫 BLOCKED IMAGES:")
        for name in results_summary["BLOCK"]:
            print(f"      • {name}")
        print()

    if results_summary["REVIEW"]:
        print("   ⚠️  IMAGES FOR REVIEW:")
        for name in results_summary["REVIEW"]:
            print(f"      • {name}")
        print()

    print("=" * 100)
    print("  ANALYSIS COMPLETE")
    print("=" * 100)

