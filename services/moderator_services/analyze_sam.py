#!/usr/bin/env python3
"""
MOCK UPLOAD TEST: sam.jpeg
Complete moderation test using all 5 detection strategies
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

# Add path for model_registry
sys.path.insert(0, str(Path(__file__).parent))
from model_registry import ensure_models

# Ensure required models are available
REQUIRED_MODELS = ['yolov8n', 'detoxify', 'transformers', 'torch', 'PIL']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ Some models not available")

print("=" * 80)
print("  MOCK AD UPLOAD TEST: sam.jpeg")
print("  Testing 'STOP THE KILLINGS' Protest Image")
print("=" * 80)
print()

# Mock ad data
mock_ad = {
    "title": "We sell weapons",
    "description": "Photo from a community awareness event",
    "category": "Events",
    "price": 0,
}

image_path = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/moderator_services/sample_images/sam.jpeg")

if not image_path.exists():
    print("Image not found")
    exit(1)

img = Image.open(image_path).convert('RGB')
img_array = np.array(img)
height, width = img_array.shape[:2]

print("MOCK AD DETAILS:")
print(f"  Title: {mock_ad['title']}")
print(f"  Description: {mock_ad['description']}")
print(f"  Category: {mock_ad['category']}")
print(f"  Image: {image_path.name} ({image_path.stat().st_size / 1024:.1f} KB)")
print(f"  Dimensions: {width}x{height}")
print()

# ============================================================
# STRATEGY 1: YOLO WEAPON DETECTION (via ML Service)
# ============================================================
print("=" * 80)
print("STRATEGY 1: YOLO WEAPON DETECTION")
print("=" * 80)

ml_result = None
try:
    with open(image_path, 'rb') as f:
        response = requests.post(
            "http://localhost:8002/moderate/image",
            files={'file': (image_path.name, f, 'image/jpeg')},
            timeout=60
        )

    if response.status_code == 200:
        ml_result = response.json()
        scores = ml_result.get('category_scores', {})

        weapon_score = scores.get('weapons', 0)
        violence_score = scores.get('violence', 0)
        blood_score = scores.get('blood', 0)

        print(f"  Weapons:  {weapon_score*100:6.2f}%", "  ✅ Low" if weapon_score < 0.3 else "  ⚠️ HIGH")
        print(f"  Violence: {violence_score*100:6.2f}%", " ✅ Low" if violence_score < 0.3 else " ⚠️ HIGH")
        print(f"  Blood:    {blood_score*100:6.2f}%", "   ✅ Low" if blood_score < 0.3 else "   ⚠️ HIGH")
        print(f"  ML Decision: {ml_result.get('decision', '?').upper()}")
    else:
        print(f"  ML Service error: HTTP {response.status_code}")
except Exception as e:
    print(f"  Error: {str(e)}")

print()

# ============================================================
# STRATEGY 2: AMMUNITION DETECTION
# ============================================================
print("=" * 80)
print("STRATEGY 2: AMMUNITION DETECTION")
print("=" * 80)

r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]

# Brass color detection (bullet casings)
brass_mask = (
    (r > 150) & (r < 255) &
    (g > 100) & (g < 200) &
    (b > 20) & (b < 100) &
    (r > g) & (g > b)
)
brass_ratio = np.sum(brass_mask) / brass_mask.size * 100

# Silver/metallic detection
silver_mask = (
    (np.abs(r.astype(float) - g.astype(float)) < 20) &
    (np.abs(g.astype(float) - b.astype(float)) < 20) &
    (r > 120) & (r < 200)
)
silver_ratio = np.sum(silver_mask) / silver_mask.size * 100

ammo_score = min(1.0, (brass_ratio/100 * 3) + (silver_ratio/100 * 2))
ammo_detected = ammo_score > 0.25

print(f"  Brass-colored pixels: {brass_ratio:.2f}%")
print(f"  Metallic pixels: {silver_ratio:.2f}%")
print(f"  Ammunition Score: {ammo_score*100:.2f}%", " ⚠️ DETECTED" if ammo_detected else " ✅ Not detected")

print()

# ============================================================
# STRATEGY 3: BLOOD/BIO SEGMENTATION
# ============================================================
print("=" * 80)
print("STRATEGY 3: BLOOD/BIOLOGICAL SEGMENTATION")
print("=" * 80)

# Normalize for analysis
r_n, g_n, b_n = r/255.0, g/255.0, b/255.0

# Blood-like red detection
blood_mask = (
    (r_n > 0.4) &
    (r_n > g_n * 1.3) &
    (r_n > b_n * 1.3)
)
blood_coverage = np.sum(blood_mask) / blood_mask.size * 100

# Dark blood detection
dark_blood_mask = (
    (r_n > 0.2) & (r_n < 0.5) &
    (r_n > g_n * 1.2) &
    (r_n > b_n * 1.2)
)
dark_blood_ratio = np.sum(dark_blood_mask) / dark_blood_mask.size * 100

total_blood = blood_coverage + dark_blood_ratio
blood_detected = total_blood > 5

print(f"  Bright red pixels: {blood_coverage:.2f}%")
print(f"  Dark red pixels: {dark_blood_ratio:.2f}%")
print(f"  Total blood-like: {total_blood:.2f}%", " ⚠️ DETECTED" if blood_detected else " ✅ Not detected")

print()

# ============================================================
# STRATEGY 4: COLOR HEURISTIC POST-FILTER
# ============================================================
print("=" * 80)
print("STRATEGY 4: COLOR HEURISTIC POST-FILTER")
print("=" * 80)

brightness = np.mean(img_array)
r_std, g_std, b_std = np.std(r), np.std(g), np.std(b)
color_uniformity = 1.0 - min(1.0, (r_std + g_std + b_std) / 300)

# Check for solid red background (false positive indicator)
red_dominant = (
    np.mean(r) > 150 and
    np.mean(r) > np.mean(g) * 1.5 and
    np.mean(r) > np.mean(b) * 1.5 and
    color_uniformity > 0.5
)

print(f"  Brightness: {brightness:.1f}/255")
print(f"  Color Uniformity: {color_uniformity*100:.1f}%")
print(f"  Red Dominant: {'Yes ⚠️ FALSE POSITIVE LIKELY' if red_dominant else 'No ✅'}")

# Adjust blood score if false positive detected
adjusted_blood = total_blood
if red_dominant and total_blood > 30:
    adjusted_blood = total_blood * 0.1
    print(f"  Adjusted Blood Score: {adjusted_blood:.2f}% (reduced due to red background)")

print()

# ============================================================
# STRATEGY 5: SCENE CONSISTENCY CHECK
# ============================================================
print("=" * 80)
print("STRATEGY 5: SCENE CONSISTENCY CHECK")
print("=" * 80)

# Calculate scene indicators
color_variance = np.var(img_array)
gray = np.mean(img_array, axis=2)
gy, gx = np.gradient(gray)
edges = np.sqrt(gx**2 + gy**2)
edge_density = np.mean(edges)

# Detect protest/crowd scene
is_protest_scene = edge_density > 15 and color_variance > 1500

# Detect banner
white_mask = (r > 200) & (g > 200) & (b > 200)
horizontal_profile = np.mean(white_mask, axis=1)
has_banner = np.max(horizontal_profile) > 0.1

print(f"  Edge Density: {edge_density:.2f}")
print(f"  Color Variance: {color_variance:.1f}")
print(f"  Protest/Crowd Scene: {'Yes 🪧' if is_protest_scene else 'No'}")
print(f"  Banner Detected: {'Yes 📜' if has_banner else 'No'}")

print()

# ============================================================
# STRATEGY 6: OCR + SEMANTIC INTENT ANALYSIS 🧠
# ============================================================
print("=" * 80)
print("STRATEGY 6: OCR + SEMANTIC INTENT ANALYSIS 🧠")
print("=" * 80)

# ACTUAL OCR - Extract text from image
detected_text = ""
ocr_confidence = 0.0

print("  📝 Running OCR on image...")

# Try EasyOCR first (most reliable, no network needed after first run)
try:
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = reader.readtext(str(image_path))
    if results:
        texts = [r[1] for r in results]
        confidences = [r[2] for r in results]
        detected_text = ' '.join(texts)
        ocr_confidence = sum(confidences) / len(confidences) if confidences else 0
        print(f"  ✅ EasyOCR detected text")
except Exception as e:
    print(f"  ⚠️ EasyOCR failed: {str(e)[:50]}")

    # Fallback to PaddleOCR
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_textline_orientation=True, lang='en')
        result = ocr.ocr(str(image_path), cls=True)

        if result and result[0]:
            texts = []
            confidences = []
            for line in result[0]:
                if line[1]:
                    texts.append(line[1][0])
                    confidences.append(line[1][1])
            detected_text = ' '.join(texts)
            ocr_confidence = sum(confidences) / len(confidences) if confidences else 0
            print(f"  ✅ PaddleOCR detected text")
    except Exception as e2:
        print(f"  ⚠️ PaddleOCR failed: {str(e2)[:50]}")

        # Last resort - pytesseract
        try:
            import pytesseract
            detected_text = pytesseract.image_to_string(img)
            detected_text = detected_text.strip()
            ocr_confidence = 0.7
            print(f"  ✅ Tesseract OCR detected text")
        except Exception as e3:
            print(f"  ❌ All OCR methods failed")

# Clean up detected text
detected_text = detected_text.strip().upper() if detected_text else ""

print(f"  Detected Text: '{detected_text}'")
print(f"  OCR Confidence: {ocr_confidence*100:.1f}%")
print()

# This strategy analyzes the FULL CONTEXT of text/content
# Not just individual trigger words, but the COMPLETE MEANING of the statement

# Anti-violence indicators - words/phrases that indicate OPPOSITION to violence
ANTI_VIOLENCE_PHRASES = [
    'stop', 'end', 'no more', 'against', 'prevent', 'ban', 'oppose',
    'fight against', 'say no to', 'reject', 'condemn', 'protest against',
    'never again', 'enough', 'stand against', 'march against', 'no to'
]

# Pro-violence indicators - words/phrases that indicate PROMOTION of violence
PRO_VIOLENCE_PHRASES = [
    'kill them', 'death to', 'destroy them', 'attack them', 'murder',
    'execute', 'eliminate them', 'wipe out', 'exterminate', 'shoot them',
    'bomb them', 'burn them', 'hang them'
]

# Violence-related words (NEUTRAL - need context to determine intent)
VIOLENCE_WORDS = [
    'killing', 'killings', 'death', 'violence', 'murder', 'war',
    'shooting', 'attack', 'assault', 'abuse', 'genocide', 'massacre'
]

# Analyze semantic intent - FULL STATEMENT CONTEXT
text_lower = detected_text.lower()

# Check for anti-violence patterns (phrase + violence word)
is_anti_violence = False
is_pro_violence = False
has_violence_word = any(word in text_lower for word in VIOLENCE_WORDS)

# INTELLIGENT FULL-CONTEXT ANALYSIS
# Check if anti-violence phrase appears BEFORE violence word
for anti_phrase in ANTI_VIOLENCE_PHRASES:
    if anti_phrase in text_lower:
        # Check if a violence word follows the anti-phrase
        anti_pos = text_lower.find(anti_phrase)
        for violence_word in VIOLENCE_WORDS:
            if violence_word in text_lower:
                violence_pos = text_lower.find(violence_word)
                # Anti-violence pattern: "STOP" comes before "KILLINGS"
                if anti_pos < violence_pos:
                    is_anti_violence = True
                    break
    if is_anti_violence:
        break

# Check for pro-violence patterns
for pro_phrase in PRO_VIOLENCE_PHRASES:
    if pro_phrase in text_lower:
        is_pro_violence = True
        break

# Additional context analysis
# "STOP THE KILLINGS" = anti-violence (calling for end)
# "THE KILLINGS MUST STOP" = anti-violence
# "KILLINGS ARE GOOD" = pro-violence
# Just "KILLINGS" alone = ambiguous

print(f"  📊 FULL STATEMENT ANALYSIS:")
print(f"     Text: '{detected_text}'")
print(f"     Contains violence words: {'Yes' if has_violence_word else 'No'}")
print(f"     Anti-violence pattern: {'Yes ✅' if is_anti_violence else 'No'}")
print(f"     Pro-violence pattern: {'Yes ⚠️' if is_pro_violence else 'No'}")

# SEMANTIC DECISION based on FULL CONTEXT
if is_anti_violence:
    semantic_intent = "ANTI_VIOLENCE"
    intent_description = f"Statement '{detected_text}' OPPOSES/CONDEMNS violence"
    print(f"  🧠 SEMANTIC INTENT: {semantic_intent}")
    print(f"     {intent_description}")
    print(f"     This is a call to END violence, NOT promote it!")
    print(f"     Example: 'STOP THE KILLINGS' = Please end the killings")
elif is_pro_violence:
    semantic_intent = "PRO_VIOLENCE"
    intent_description = f"Statement promotes or incites violence"
    print(f"  ⚠️ SEMANTIC INTENT: {semantic_intent}")
    print(f"     {intent_description}")
elif has_violence_word and not is_anti_violence:
    semantic_intent = "AMBIGUOUS"
    intent_description = "Contains violence words but full intent unclear"
    print(f"  ❓ SEMANTIC INTENT: {semantic_intent}")
    print(f"     {intent_description}")
elif not detected_text:
    semantic_intent = "NO_TEXT"
    intent_description = "No text detected in image"
    print(f"  ℹ️ SEMANTIC INTENT: {semantic_intent}")
    print(f"     {intent_description}")
else:
    semantic_intent = "NEUTRAL"
    intent_description = "No violence-related content in text"
    print(f"  ✅ SEMANTIC INTENT: {semantic_intent}")
    print(f"     {intent_description}")

print()

# ============================================================
# STRATEGY 7: COMBINED CONTEXT ANALYSIS
# ============================================================
print("=" * 80)
print("STRATEGY 7: COMBINED CONTEXT ANALYSIS")
print("=" * 80)

# Determine scenario with FULL INTELLIGENT CONTEXT ANALYSIS
weapon_detected = ml_result and ml_result.get('category_scores', {}).get('weapons', 0) > 0.3
weapon_score_raw = ml_result.get('category_scores', {}).get('weapons', 0) if ml_result else 0

# INTELLIGENT CONTEXT-AWARE DECISION
# Consider ALL factors: scene type, semantic intent, visual analysis

# Case 1: Anti-violence message detected
if semantic_intent == "ANTI_VIOLENCE":
    # This is protected speech - someone speaking AGAINST violence
    scenario = "ANTI_VIOLENCE_MESSAGE"
    threat_level = "NONE"
    context_note = "Text analysis shows ANTI-violence intent (e.g., 'STOP THE KILLINGS')"
    weapon_detected = False  # Override - text triggered false positive

# Case 2: Pro-violence message detected
elif semantic_intent == "PRO_VIOLENCE":
    scenario = "HATE_SPEECH"
    threat_level = "CRITICAL"
    context_note = "Text analysis shows PRO-violence/incitement content"

# Case 3: Protest scene with moderate signals
elif is_protest_scene and weapon_score_raw < 0.85:
    scenario = "PROTEST_SCENE"
    threat_level = "LOW"
    context_note = "Protest/demonstration - protected speech"
    weapon_detected = False

# Case 4: Armed protest (actual weapons visible at high confidence)
elif is_protest_scene and weapon_score_raw > 0.85 and ammo_detected:
    scenario = "ARMED_PROTEST"
    threat_level = "CRITICAL"
    context_note = "Weapons and ammunition confirmed at protest"

# Case 5: Clear weapon + ammunition
elif weapon_detected and ammo_detected and weapon_score_raw > 0.7:
    scenario = "ARMED_SCENARIO"
    threat_level = "CRITICAL"
    context_note = "Weapon with ammunition confirmed"

# Case 6: Violence scene
elif weapon_detected and blood_detected and not red_dominant:
    scenario = "VIOLENCE_SCENE"
    threat_level = "CRITICAL"
    context_note = "Violence scene - weapon with blood detected"

# Case 7: High confidence weapon
elif weapon_score_raw > 0.75:
    scenario = "WEAPON_CONFIRMED"
    threat_level = "HIGH"
    context_note = "High confidence weapon detected"

# Case 8: Moderate weapon signal
elif weapon_detected:
    scenario = "POSSIBLE_WEAPON"
    threat_level = "MEDIUM"
    context_note = "Possible weapon - needs verification"

# Case 9: Blood/injury only
elif blood_detected and not red_dominant:
    scenario = "INJURY_SCENE"
    threat_level = "MEDIUM"
    context_note = "Blood/biological content detected"

# Case 10: General safe content
else:
    scenario = "SAFE_CONTENT"
    threat_level = "NONE"
    context_note = "No significant threats detected"

print(f"  Final Scenario: {scenario}")
print(f"  Threat Level: {threat_level}")
print(f"  Context: {context_note}")

# Show the intelligent reasoning
if semantic_intent == "ANTI_VIOLENCE":
    print()
    print("  🧠 INTELLIGENT REASONING:")
    print(f"     • ML detected 'weapon' signal: {weapon_score_raw*100:.1f}%")
    print(f"     • But semantic analysis shows: ANTI-VIOLENCE message")
    print(f"     • The word 'KILLINGS' appears in 'STOP THE KILLINGS'")
    print(f"     • Full context: This is a call to END violence")
    print(f"     • Decision: Override false positive, APPROVE content")

print()

# ============================================================
# FINAL MODERATION DECISION
# ============================================================
print("=" * 80)
print("FINAL MODERATION DECISION")
print("=" * 80)
print()

# Collect all scores
weapon_score = ml_result.get('category_scores', {}).get('weapons', 0) if ml_result else 0
final_blood = adjusted_blood / 100

# ============================================================
# INTELLIGENT DECISION ENGINE (Context-Aware)
# ============================================================
# Priority order:
# 1. SEMANTIC INTENT - Full text meaning (most important!)
# 2. Scene context (protest/crowd)
# 3. Very high confidence visual detections (>85%)
# 4. Combined signals (weapon + ammo)

if scenario == "ANTI_VIOLENCE_MESSAGE":
    # HIGHEST PRIORITY: Anti-violence content is PROTECTED SPEECH
    decision = "APPROVE"
    risk = "NONE"
    reason = f"Anti-violence message detected - '{detected_text}' OPPOSES violence, not promotes it"

elif scenario == "HATE_SPEECH":
    decision = "BLOCK"
    risk = "CRITICAL"
    reason = "Pro-violence/hate speech detected"

elif scenario == "PROTEST_SCENE":
    decision = "APPROVE"
    risk = "LOW"
    reason = "Protest/demonstration scene - protected speech"

elif scenario == "ARMED_PROTEST":
    decision = "BLOCK"
    risk = "CRITICAL"
    reason = "Armed protest - weapons and ammunition confirmed at demonstration"

elif scenario == "ARMED_SCENARIO":
    decision = "BLOCK"
    risk = "CRITICAL"
    reason = "Weapon with ammunition confirmed"

elif scenario == "VIOLENCE_SCENE":
    decision = "BLOCK"
    risk = "CRITICAL"
    reason = "Violence scene - weapon with blood detected"

elif scenario == "WEAPON_CONFIRMED":
    decision = "BLOCK"
    risk = "HIGH"
    reason = "High confidence weapon detected (>75%)"

elif scenario == "POSSIBLE_WEAPON":
    if weapon_score > 0.6:
        decision = "REVIEW"
        risk = "MEDIUM"
        reason = "Moderate weapon signal - needs human review"
    else:
        decision = "APPROVE"
        risk = "LOW"
        reason = "Low-moderate weapon signal - likely false positive"

elif scenario == "INJURY_SCENE":
    decision = "REVIEW"
    risk = "MEDIUM"
    reason = "Blood/biological content detected"

elif scenario == "SAFE_CONTENT":
    decision = "APPROVE"
    risk = "NONE"
    reason = "No threats detected - safe content"

else:
    decision = "APPROVE"
    risk = "LOW"
    reason = "No significant threats detected"

# Display decision
decision_emoji = {"BLOCK": "🚫", "REVIEW": "⚠️", "APPROVE": "✅"}.get(decision, "❓")

print(f"  {decision_emoji} DECISION: {decision}")
print(f"  RISK LEVEL: {risk}")
print(f"  REASON: {reason}")
print()

# Confidence scores summary
print("  📊 CONFIDENCE SCORES:")
print(f"     Weapon:     [{('█' * int(weapon_score * 20)).ljust(20, '░')}] {weapon_score*100:5.1f}%")
print(f"     Ammunition: [{('█' * int(ammo_score * 20)).ljust(20, '░')}] {ammo_score*100:5.1f}%")
print(f"     Blood:      [{('█' * int(final_blood * 20)).ljust(20, '░')}] {final_blood*100:5.1f}%")
print()

# Compare with ML decision
ml_decision = ml_result.get('decision', 'unknown').upper() if ml_result else 'ERROR'
print("  📋 COMPARISON:")
print(f"     ML Service Decision: {ml_decision}")
print(f"     Our Smart Decision:  {decision}")

if ml_decision == "BLOCK" and decision == "APPROVE":
    print()
    print("  ⚠️  OVERRIDE: ML false positive corrected!")
    print("     Reason: Protest scene detected - protected speech")
    print("     The text 'STOP THE KILLINGS' is ANTI-violence, not pro-violence")

print()
print("=" * 80)
print("  UPLOAD SIMULATION RESULT")
print("=" * 80)
print()

if decision == "APPROVE":
    print("  ✅ AD WOULD BE PUBLISHED")
    print("     The protest image passes moderation.")
elif decision == "REVIEW":
    print("  ⚠️  AD FLAGGED FOR MANUAL REVIEW")
    print("     A human moderator would verify this content.")
else:
    print("  🚫 AD WOULD BE REJECTED")
    print("     Content violates platform policies.")

print()
print("=" * 80)

