"""
Content Moderation Service for EcoGreen produce listings.

Supported engines (set MODERATION_MODE in .env):
  simulate  -> Keyword/filename checks only. No API key needed. Used for tests.
  gemini    -> Google Gemini Vision API (FREE tier). Needs GEMINI_API_KEY.
  claude    -> Anthropic Claude Vision API (paid). Needs ANTHROPIC_API_KEY.

Decision values returned:
  'approved'     -> image matches declared name/category, product can be listed
  'rejected'     -> image is wrong item, prohibited, or unrelated (HTTP 422)
  'needs_review' -> ambiguous / too blurry for confidence (HTTP 202)
  'unavailable'  -> API call failed / timed out (HTTP 503, never silently approve)
"""

import json
import re
import base64
import logging
import requests as _requests

from backend.app.config import Config

logger = logging.getLogger(__name__)

# ─── Keyword lists for SIMULATE mode ────────────────────────────────────────

PROHIBITED_KEYWORDS = [
    'laptop', 'phone', 'iphone', 'ipad', 'computer', 'electronic', 'electronics',
    'drug', 'drugs', 'weapon', 'weapons', 'gun', 'guns', 'pistol', 'prohibited',
    'test_reject', 'laptop_photo',
]

NEEDS_REVIEW_KEYWORDS = [
    'test_review', 'test_needs_review', 'ambiguous', 'low_quality',
]

# Recognisable farm-produce keywords for filename cross-check
_ITEM_KEYWORDS = ['tomato', 'carrot', 'honey', 'egg', 'apple', 'banana', 'grain', 'orange']


# ─── Shared prompt for vision models ────────────────────────────────────────

_VISION_SYSTEM_PROMPT = """\
You are a strict content moderation AI for EcoGreen, an agricultural direct-from-farmer marketplace.
Your ONLY job is to decide whether a product image matches the farmer's declared product name and category.

ALLOWED: Fresh vegetables, fruits, dairy & eggs, honey, grains, spices, or any legitimate farm produce.
PROHIBITED: Electronics, weapons, drugs, nudity, violence, random unrelated objects.

You will receive:
  - A declared product name (e.g. "orange", "tomatoes", "A2 ghee")
  - A declared category (e.g. "Fruits", "Vegetables", "Dairy & Eggs")
  - An image to evaluate

Respond ONLY with a single valid JSON object — no markdown fences, no extra text:

{
  "detected_content": "<one-sentence description of what the image actually shows>",
  "matches_declared_name": <true if image clearly shows the declared product, false otherwise>,
  "matches_declared_category": <true if image is broadly in the correct category>,
  "is_prohibited_or_unrelated": <true if electronics/weapons/drugs/nudity/violence/random object>,
  "decision": "<approved|rejected|needs_review>",
  "reason": "<one human-readable sentence explaining the decision>"
}

Decision rules (apply strictly in order):
1. If is_prohibited_or_unrelated is true -> decision = "rejected"
2. If matches_declared_name is false AND the image clearly shows a DIFFERENT specific item
   (e.g. image is clearly an apple but declared name is "orange") -> decision = "rejected"
   Reason must explicitly name what was found vs what was declared.
3. If matches_declared_name is true AND matches_declared_category is true -> decision = "approved"
4. If the image is too blurry, too dark, or genuinely ambiguous -> decision = "needs_review"
"""


# ─── Public entry point ──────────────────────────────────────────────────────

def moderate_product_image(image_input, declared_category='Vegetables', declared_name='Fresh Produce'):
    """
    Synchronously evaluate a product image + declared metadata.

    Returns a dict with keys:
        decision                  : 'approved' | 'rejected' | 'needs_review' | 'unavailable'
        detected_content          : str
        matches_declared_name     : bool
        matches_declared_category : bool
        is_prohibited_or_unrelated: bool
        reason                    : str (human-readable, shown in UI)
        raw_model_output          : str (raw JSON from model)
    """
    from flask import current_app, has_app_context

    # Prefer app-context config so pytest fixtures can override MODERATION_MODE
    if has_app_context():
        mode = str(current_app.config.get('MODERATION_MODE', 'simulate')).lower()
        gemini_key = str(current_app.config.get('GEMINI_API_KEY') or '')
        gemini_model = str(current_app.config.get('GEMINI_MODEL') or 'gemini-3.5-flash-lite')
        anthropic_key = str(current_app.config.get('ANTHROPIC_API_KEY') or '')
        claude_model = str(current_app.config.get('MODERATION_MODEL') or 'claude-sonnet-4-6')
    else:
        mode = getattr(Config, 'MODERATION_MODE', 'simulate').lower()
        gemini_key = getattr(Config, 'GEMINI_API_KEY', '')
        gemini_model = getattr(Config, 'GEMINI_MODEL', 'gemini-3.5-flash-lite')
        anthropic_key = getattr(Config, 'ANTHROPIC_API_KEY', '')
        claude_model = getattr(Config, 'MODERATION_MODEL', 'claude-sonnet-4-6')

    # Graceful fallbacks if key is missing
    if mode == 'gemini' and not gemini_key:
        logger.warning("MODERATION_MODE='gemini' but GEMINI_API_KEY empty. Falling back to simulate.")
        mode = 'simulate'
    elif mode == 'claude' and not anthropic_key:
        logger.warning("MODERATION_MODE='claude' but ANTHROPIC_API_KEY empty. Falling back to simulate.")
        mode = 'simulate'

    if mode == 'gemini':
        return _gemini_moderation(image_input, declared_category, declared_name, gemini_key, gemini_model)
    elif mode == 'claude':
        return _claude_moderation(image_input, declared_category, declared_name, anthropic_key, claude_model)
    else:
        return _simulate_moderation(image_input, declared_category, declared_name)


# ─── Simulate engine (no network, deterministic) ─────────────────────────────

def _simulate_moderation(image_input, declared_category, declared_name):
    """Keyword/filename-based engine for tests and when no API key is set."""
    file_name = getattr(image_input, 'filename', '') or str(image_input)
    combined_text = f"{declared_name} {declared_category} {file_name}".lower()

    if 'simulate_error' in combined_text or 'service_error' in combined_text:
        return _unavailable_result("Simulated Error")

    for kw in PROHIBITED_KEYWORDS:
        if kw in combined_text:
            reason = (
                f"This image doesn't show a valid farm product and cannot be listed. "
                f"Prohibited keyword '{kw}' detected (Simulated Check)."
            )
            return {
                'decision': 'rejected',
                'detected_content': f'non-farm item ({kw})',
                'matches_declared_name': False,
                'matches_declared_category': False,
                'is_prohibited_or_unrelated': True,
                'reason': reason,
                'raw_model_output': json.dumps({'simulated': True, 'keyword': kw, 'decision': 'rejected'}),
            }

    if 'test_mismatch' in combined_text or 'mismatch' in combined_text:
        detected = 'apple' if 'orange' in declared_name.lower() else 'carrot'
        reason = (
            f"The photo doesn't look like '{declared_name}' \u2014 it looks like {detected}. "
            f"Please upload a matching photo or correct the product name. (Simulated Check)."
        )
        return {
            'decision': 'rejected',
            'detected_content': detected,
            'matches_declared_name': False,
            'matches_declared_category': True,
            'is_prohibited_or_unrelated': False,
            'reason': reason,
            'raw_model_output': json.dumps({'simulated': True, 'mismatch': True, 'decision': 'rejected'}),
        }

    # Cross-check item keywords in filename vs declared name
    declared_items = [k for k in _ITEM_KEYWORDS if k in declared_name.lower()]
    file_items = [k for k in _ITEM_KEYWORDS if k in file_name.lower()]
    if declared_items and file_items and not any(k in file_items for k in declared_items):
        detected = file_items[0]
        reason = (
            f"The photo doesn't look like '{declared_name}' \u2014 it looks like {detected}. "
            f"Please upload a matching photo or correct the product name. (Simulated Check)."
        )
        return {
            'decision': 'rejected',
            'detected_content': detected,
            'matches_declared_name': False,
            'matches_declared_category': True,
            'is_prohibited_or_unrelated': False,
            'reason': reason,
            'raw_model_output': json.dumps({'simulated': True, 'mismatch': True, 'decision': 'rejected'}),
        }

    for kw in NEEDS_REVIEW_KEYWORDS:
        if kw in combined_text:
            return {
                'decision': 'needs_review',
                'detected_content': 'Ambiguous or low-quality image placeholder',
                'matches_declared_name': False,
                'matches_declared_category': False,
                'is_prohibited_or_unrelated': False,
                'reason': f"Listing '{declared_name}' flagged for manual review (Simulated Check).",
                'raw_model_output': json.dumps({'simulated': True, 'keyword': kw, 'decision': 'needs_review'}),
            }

    return {
        'decision': 'approved',
        'detected_content': declared_name or 'Fresh Farm Produce',
        'matches_declared_name': True,
        'matches_declared_category': True,
        'is_prohibited_or_unrelated': False,
        'reason': f"Verified produce item '{declared_name}' (Simulated Check).",
        'raw_model_output': json.dumps({'simulated': True, 'decision': 'approved'}),
    }


# ─── Image encoding helpers ──────────────────────────────────────────────────

def _to_base64_and_mime(image_input):
    """Convert file-like / URL / data-URI / bytes to (base64_str, mime_type)."""
    try:
        if isinstance(image_input, (bytes, bytearray)):
            raw = bytes(image_input)
            mime = 'image/jpeg'
            if raw.startswith(b'\x89PNG'):
                mime = 'image/png'
            elif raw.startswith(b'GIF8'):
                mime = 'image/gif'
            elif raw.startswith(b'RIFF') and b'WEBP' in raw[:16]:
                mime = 'image/webp'
            return base64.b64encode(raw).decode(), mime

        if hasattr(image_input, 'read'):
            raw = image_input.read()
            if hasattr(image_input, 'seek'):
                image_input.seek(0)
            mime = getattr(image_input, 'mimetype', None) or 'image/jpeg'
            if raw.startswith(b'\x89PNG'):
                mime = 'image/png'
            elif raw.startswith(b'GIF8'):
                mime = 'image/gif'
            elif raw.startswith(b'RIFF') and b'WEBP' in raw[:16]:
                mime = 'image/webp'
            return base64.b64encode(raw).decode(), mime

        if isinstance(image_input, str):
            if image_input.startswith('data:'):
                m = re.match(r'data:([^;]+);base64,(.+)', image_input, re.DOTALL)
                if m:
                    return m.group(2), m.group(1)
                return None, None
            if image_input.startswith(('http://', 'https://')):
                resp = _requests.get(image_input, timeout=8)
                if resp.status_code == 200:
                    mime = resp.headers.get('Content-Type', 'image/jpeg').split(';')[0]
                    return base64.b64encode(resp.content).decode(), mime
    except Exception as exc:
        logger.warning(f"[Moderation] Could not encode image: {exc}")
    return None, None


# ─── Gemini Vision engine ─────────────────────────────────────────────────────

def _gemini_moderation(image_input, declared_category, declared_name, api_key, model_name):
    """
    Call Google Gemini Vision via the google-generativeai SDK.
    Free tier: 15 RPM, 1 M tokens/day for gemini-2.0-flash.
    """
    try:
        import google.generativeai as genai
        from google.generativeai import types as genai_types

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)

        user_text = (
            f'Declared product name: "{declared_name}"\n'
            f'Declared category: "{declared_category}"\n\n'
            f'{_VISION_SYSTEM_PROMPT}\n\n'
            f'Evaluate the image and return ONLY the JSON object described above.'
        )

        b64_data, mime_type = _to_base64_and_mime(image_input)

        parts = []
        if b64_data and mime_type:
            parts.append({'mime_type': mime_type, 'data': b64_data})
        else:
            logger.warning(
                f"[Moderation GEMINI] Cannot encode image for '{declared_name}'. "
                "Treating as needs_review."
            )
        parts.append(user_text)

        response = model.generate_content(parts, request_options={'timeout': 15})
        raw_text = response.text if hasattr(response, 'text') else ''
        logger.info(f"[Moderation GEMINI] Raw for '{declared_name}': {raw_text[:300]}")
        return _parse_moderation_json(raw_text, declared_name)

    except Exception as exc:
        err = str(exc)
        logger.error(f"[Moderation GEMINI] Error for '{declared_name}': {err}")
        return _unavailable_result(err)


# ─── Claude Vision engine ─────────────────────────────────────────────────────

def _claude_moderation(image_input, declared_category, declared_name, api_key, model_name):
    """Call Anthropic Claude Vision API."""
    b64_data, mime_type = _to_base64_and_mime(image_input)
    user_text = (
        f'Declared product name: "{declared_name}"\n'
        f'Declared category: "{declared_category}"\n\n'
        f'Evaluate the image and return your JSON verdict.'
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        content_blocks = []
        if b64_data and mime_type:
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime_type, "data": b64_data},
            })
        else:
            logger.warning(f"[Moderation CLAUDE] Cannot encode image for '{declared_name}'.")
        content_blocks.append({"type": "text", "text": user_text})

        response = client.messages.create(
            model=model_name,
            max_tokens=512,
            timeout=15,
            system=_VISION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content_blocks}],
        )
        raw_text = response.content[0].text if response.content else ''
        logger.info(f"[Moderation CLAUDE] Raw for '{declared_name}': {raw_text[:300]}")
        return _parse_moderation_json(raw_text, declared_name)

    except Exception as exc:
        err = str(exc)
        logger.error(f"[Moderation CLAUDE] Error for '{declared_name}': {err}")
        return _unavailable_result(err)


# ─── JSON parsing ─────────────────────────────────────────────────────────────

def _parse_moderation_json(raw_text, declared_name):
    """
    Parse the JSON response from a vision model.
    Strips markdown fences. On parse failure -> needs_review (never 'approved').
    Also enforces: if matches_declared_name=False -> decision='rejected' always.
    """
    cleaned = raw_text.strip()
    cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned.strip()).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"[Moderation] JSON parse failed for '{declared_name}'. Raw: {raw_text[:200]}")
        return {
            'decision': 'needs_review',
            'detected_content': 'Could not parse AI response',
            'matches_declared_name': False,
            'matches_declared_category': False,
            'is_prohibited_or_unrelated': False,
            'reason': 'AI response could not be parsed. Queued for manual admin review.',
            'raw_model_output': raw_text,
        }

    decision = str(parsed.get('decision', 'needs_review')).lower()
    if decision not in ('approved', 'rejected', 'needs_review'):
        decision = 'needs_review'

    is_prohibited = bool(parsed.get('is_prohibited_or_unrelated', False))
    matches_name = bool(parsed.get('matches_declared_name', True))

    # Hard rule: prohibited or name mismatch -> always rejected
    if is_prohibited or not matches_name:
        decision = 'rejected'

    return {
        'decision': decision,
        'detected_content': str(parsed.get('detected_content', 'Unknown content')),
        'matches_declared_name': matches_name,
        'matches_declared_category': bool(parsed.get('matches_declared_category', True)),
        'is_prohibited_or_unrelated': is_prohibited,
        'reason': str(parsed.get('reason', 'Moderation evaluation completed.')),
        'raw_model_output': raw_text,
    }


def _unavailable_result(error_detail=''):
    return {
        'decision': 'unavailable',
        'detected_content': 'AI Service Error',
        'matches_declared_name': False,
        'matches_declared_category': False,
        'is_prohibited_or_unrelated': False,
        'reason': "We couldn't verify your image right now. Please try again.",
        'raw_model_output': error_detail,
    }
