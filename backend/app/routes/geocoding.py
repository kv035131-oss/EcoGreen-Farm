"""
Reverse Geocoding Endpoint using OpenStreetMap Nominatim API with Throttling & Caching.
"""

import time
import requests
import logging
from flask import Blueprint, request, jsonify

geocoding_bp = Blueprint('geocoding_bp', __name__)
logger = logging.getLogger(__name__)

# Server-side 24-hour cache: (round(lat, 3), round(lon, 3)) -> (timestamp, data_dict)
_GEO_CACHE = {}
_LAST_REQ_TIMESTAMP = 0.0

@geocoding_bp.route('/api/v1/geocode/reverse', methods=['POST'])
def reverse_geocode():
    """
    Reverse geocodes latitude & longitude coordinates into a human-readable address.
    Complies with OpenStreetMap Nominatim Usage Policy (User-Agent header, 1 req/sec throttle, 24h cache).
    """
    global _LAST_REQ_TIMESTAMP

    data = request.json or request.form or {}
    try:
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'Valid numeric latitude and longitude coordinates are required.'
        }), 200

    cache_key = (round(lat, 3), round(lon, 3))
    now = time.time()

    # Check 24-hour cache
    if cache_key in _GEO_CACHE:
        cached_time, cached_payload = _GEO_CACHE[cache_key]
        if now - cached_time < 86400: # 24 hours in seconds
            return jsonify({
                'success': True,
                **cached_payload,
                'cached': True
            }), 200

    # Throttle: Ensure at least 1.0 second between external Nominatim API calls
    time_since_last = now - _LAST_REQ_TIMESTAMP
    if time_since_last < 1.0:
        time.sleep(1.0 - time_since_last)

    headers = {
        'User-Agent': 'EcoGreenFarmApp/1.0 (contact@ecogreen.com)'
    }
    nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"

    try:
        response = requests.get(nominatim_url, headers=headers, timeout=5)
        _LAST_REQ_TIMESTAMP = time.time()

        if response.status_code != 200:
            logger.warning(f"Nominatim returned status {response.status_code}")
            return jsonify({
                'success': False,
                'error': f"Reverse geocoding service returned HTTP {response.status_code}"
            }), 200

        geo_data = response.json()
        address_info = geo_data.get('address', {})
        display_name = geo_data.get('display_name', '')

        district = (
            address_info.get('state_district') or
            address_info.get('district') or
            address_info.get('county') or
            address_info.get('city') or
            address_info.get('town') or
            ''
        )
        state = address_info.get('state', '')
        pincode = address_info.get('postcode', '')

        if not display_name:
            return jsonify({
                'success': False,
                'error': 'No address found for specified coordinates.'
            }), 200

        result_payload = {
            'address_text': display_name,
            'district': district,
            'state': state,
            'pincode': pincode,
            'latitude': lat,
            'longitude': lon
        }

        # Save to 24h cache
        _GEO_CACHE[cache_key] = (time.time(), result_payload)

        return jsonify({
            'success': True,
            **result_payload
        }), 200

    except Exception as e:
        logger.error(f"Reverse geocoding exception: {e}")
        return jsonify({
            'success': False,
            'error': f"Geocoding request failed: {str(e)}"
        }), 200
