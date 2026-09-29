"""
Content Moderation Service for EcoGreen produce listings.
Supports SIMULATE mode and GEMINI (Google Generative AI Vision) mode.
"""

import json
import base64
import logging
import requests
from io import BytesIO

from backend.app.config import Config

logger = logging.getLogger(__name__)

PROHIBITED_KEYWORDS = [
    'laptop', 'phone', 'iphone', 'ipad', 'computer', 'electronic', 'electronics',
    'drug', 'drugs', 'weapon', 'weapons', 'gun', 'guns', 'pistol', 'prohibited',
    'test_reject', 'laptop_photo'
]

NEEDS_REVIEW_KEYWORDS = [
    'test_review', 'test_needs_review', 'ambiguous', 'low_quality'
]

def _convert_image_to_base64_and_mime(image_input):
    """
    Converts image input (bytes, BytesIO, or HTTP URL) to (base64_str, mime_type).
    """
    try:
        if isinstance(image_input, (bytes, bytearray)):
            b64 = base64.b64encode(image_input).decode('utf-8')
            return b64, 'image/jpeg'
        elif hasattr(image_input, 'read'):
            raw = image_input.read()
            if hasattr(image_input, 'seek'):
                image_input.seek(0)
            b64 = base64.b64encode(raw).decode('utf-8')
            return b64, 'image/jpeg'
        elif isinstance(image_input, str) and image_input.startswith(('http://', 'https://')):
            res = requests.get(image_input, timeout=5)
            if res.status_code == 200:
                b64 = base64.b64encode(res.content).decode('utf-8')
                content_type = res.headers.get('Content-Type', 'image/jpeg')
                return b64, content_type
    except Exception as e:
        logger.warning(f"Failed to fetch/convert image input for moderation: {e}")
    return None, None


def moderate_product_image(image_input, declared_category='Vegetables', declared_name='Fresh Produce'):
    """
    Evaluates product image & declared metadata for appropriateness.
    Returns dict:
      {
        'decision': 'approved' | 'rejected' | 'needs_review',
        'detected_content': str,
        'matches_declared_category': bool,
        'reason': str,
        'raw_model_output': str
      }
    """
    mode = getattr(Config, 'MODERATION_MODE', 'simulate').lower()
    api_key = getattr(Config, 'GEMINI_API_KEY', '')

    if mode == 'gemini' and not api_key:
        logger.warning("MODERATION_MODE is 'gemini' but GEMINI_API_KEY is missing. Falling back to 'simulate' mode.")
        mode = 'simulate'

    if mode == 'simulate':
        return _simulate_moderation(image_input, declared_category, declared_name)
    else:
        return _gemini_moderation(image_input, declared_category, declared_name, api_key)


def _simulate_moderation(image_input, declared_category, declared_name):
    """
    Deterministic rule engine for SIMULATE mode testing.
    """
    file_name = getattr(image_input, 'filename', '') or str(image_input)
    combined_text = f"{declared_name} {declared_category} {file_name}".lower()

    # Check prohibited keywords
    for keyword in PROHIBITED_KEYWORDS:
        if keyword in combined_text:
            reason = f"Listing '{declared_name}' contains prohibited non-farm item keyword '{keyword}' (Simulated Check)."
            logger.info(f"[Moderation SIMULATE] Rejected product: {reason}")
            return {
                'decision': 'rejected',
                'detected_content': f'Prohibited item / non-farm keyword ({keyword})',
                'matches_declared_category': False,
                'reason': reason,
                'raw_model_output': json.dumps({'simulated': True, 'keyword_triggered': keyword, 'decision': 'rejected'})
            }

    # Check needs_review keywords
    for keyword in NEEDS_REVIEW_KEYWORDS:
        if keyword in combined_text:
            reason = f"Listing '{declared_name}' flagged for manual review due to keyword '{keyword}' (Simulated Check)."
            logger.info(f"[Moderation SIMULATE] Needs review: {reason}")
            return {
                'decision': 'needs_review',
                'detected_content': 'Ambiguous or low quality image placeholder',
                'matches_declared_category': False,
                'reason': reason,
                'raw_model_output': json.dumps({'simulated': True, 'keyword_triggered': keyword, 'decision': 'needs_review'})
            }

    # Default approve in simulate mode
    logger.info(f"[Moderation SIMULATE] Approved product '{declared_name}' ({declared_category}).")
    return {
        'decision': 'approved',
        'detected_content': declared_name or 'Fresh Farm Produce',
        'matches_declared_category': True,
        'reason': f"Verified produce item '{declared_name}' (Simulated Check).",
        'raw_model_output': json.dumps({'simulated': True, 'decision': 'approved'})
    }


def _gemini_moderation(image_input, declared_category, declared_name, api_key):
    """
    Calls Google Gemini Vision API to moderate produce listing.
    """
    model_name = getattr(Config, 'GEMINI_MODEL', 'gemini-2.5-flash')
    
    prompt_text = f"""
You are an automated content moderation AI for an agricultural direct-from-farmer marketplace called EcoGreen.
Analyze the provided image along with the declared product details:
Declared Product Name: "{declared_name}"
Declared Category: "{declared_category}"

ALLOWED CATEGORIES: Vegetables, Fruits, Dairy & Eggs, Honey, Grains, or other legitimate fresh farm produce.
PROHIBITED CONTENT: Electronics, weapons, drugs/illegal substances, nudity/sexual content, violence, unrelated random objects, or non-farm commercial goods.

Respond with ONLY a strict JSON object with these exact keys:
{{
  "decision": "approved" | "rejected" | "needs_review",
  "detected_content": "short description of what is in the image",
  "matches_declared_category": true | false,
  "reason": "short human-readable reason"
}}

Rules for decision:
- "approved": image clearly shows real, appropriate fresh farm produce matching declared product.
- "rejected": image clearly shows prohibited, inappropriate, fake, or non-farm content (e.g. laptop, phone, weapon, drug).
- "needs_review": ambiguous image, stock photo, poor quality, or model is unsure.
"""

    b64_img, mime_type = _convert_image_to_base64_and_mime(image_input)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }

        model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)

        content_parts = [prompt_text]
        if b64_img:
            content_parts.append({
                "mime_type": mime_type or "image/jpeg",
                "data": b64_img
            })

        response = model.generate_content(content_parts, timeout=10)

        # Check safety filter blocks
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            block_reason = getattr(response.prompt_feedback, 'block_reason', None)
            if block_reason:
                return {
                    'decision': 'rejected',
                    'detected_content': 'Safety filter block',
                    'matches_declared_category': False,
                    'reason': 'Image blocked by safety filter.',
                    'raw_model_output': f"Safety block: {block_reason}"
                }

        raw_text = response.text if hasattr(response, 'text') else ''
        if not raw_text:
            return {
                'decision': 'needs_review',
                'detected_content': 'Empty response from vision model',
                'matches_declared_category': False,
                'reason': 'AI model returned empty response. Queued for manual admin review.',
                'raw_model_output': 'Empty model output'
            }

        parsed = json.loads(raw_text)
        decision = parsed.get('decision', 'needs_review').lower()
        if decision not in ['approved', 'rejected', 'needs_review']:
            decision = 'needs_review'

        return {
            'decision': decision,
            'detected_content': parsed.get('detected_content', 'Unknown content'),
            'matches_declared_category': bool(parsed.get('matches_declared_category', False)),
            'reason': parsed.get('reason', 'Moderation evaluation completed.'),
            'raw_model_output': raw_text
        }

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Gemini API Moderation Error: {err_msg}")
        
        # Check safety block in exception
        if 'safety' in err_msg.lower() or 'blocked' in err_msg.lower():
            return {
                'decision': 'rejected',
                'detected_content': 'Safety block triggered',
                'matches_declared_category': False,
                'reason': 'Image blocked by safety filter.',
                'raw_model_output': err_msg
            }

        # Fallback to needs_review (NEVER fail open to approved)
        return {
            'decision': 'needs_review',
            'detected_content': 'AI Service Error',
            'matches_declared_category': False,
            'reason': 'AI moderation service unavailable. Queued for manual admin review.',
            'raw_model_output': err_msg
        }
