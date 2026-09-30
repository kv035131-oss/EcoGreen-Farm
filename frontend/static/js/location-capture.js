/**
 * Reusable Location Capture Module for EcoGreen.
 * Handles HTML5 Geolocation API, backend reverse-geocoding, and manual fallback input.
 */

window.EcoGreenLocation = (function () {
    const instances = {};

    function init(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const instanceId = containerId;
        const hiddenLatId = options.hiddenLatId || `${instanceId}-lat`;
        const hiddenLngId = options.hiddenLngId || `${instanceId}-lng`;
        const hiddenAddressId = options.hiddenAddressId || `${instanceId}-address`;
        const hiddenDistrictId = options.hiddenDistrictId || `${instanceId}-district`;
        const hiddenStateId = options.hiddenStateId || `${instanceId}-state`;
        const manualInputId = options.manualInputId || `${instanceId}-manual`;

        instances[instanceId] = {
            containerId,
            options,
            hiddenLatId,
            hiddenLngId,
            hiddenAddressId,
            hiddenDistrictId,
            hiddenStateId,
            manualInputId
        };

        container.innerHTML = `
            <div class="location-capture-widget">
                <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                    <button type="button" class="btn btn-outline" onclick="EcoGreenLocation.capture('${instanceId}')" style="padding: 0.5rem 0.85rem; font-size: 0.85rem;">
                        <i class="fa-solid fa-location-crosshairs" style="color: var(--primary);"></i> 📍 Use My Current Location
                    </button>
                    <a href="javascript:void(0)" onclick="EcoGreenLocation.toggleManual('${instanceId}')" style="font-size: 0.8rem; color: var(--primary); text-decoration: underline; font-weight: 500;">
                        ✏️ Or Edit Address
                    </a>
                </div>

                <div id="${instanceId}-status" style="font-size: 0.82rem; margin-top: 0.4rem; color: var(--text-muted); font-weight: 500;"></div>

                <div id="${instanceId}-display-card" style="display: none; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 0.6rem 0.8rem; margin-top: 0.5rem;">
                    <div style="font-size: 0.75rem; color: #047857; font-weight: 700; text-transform: uppercase; margin-bottom: 0.2rem;">
                        <i class="fa-solid fa-circle-check"></i> Captured Address
                    </div>
                    <input type="text" id="${instanceId}-display" class="form-input" readonly style="background: transparent; border: none; font-weight: 600; color: #065f46; width: 100%; padding: 0;">
                </div>

                <div id="${instanceId}-manual-box" style="display: none; margin-top: 0.5rem;">
                    <label class="form-label" style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">Manual Address Fallback:</label>
                    <input type="text" id="${manualInputId}" class="form-input" placeholder="e.g. MG Road, Mysuru, Karnataka, 570001" oninput="EcoGreenLocation.onManualInput('${instanceId}')">
                </div>

                <!-- Hidden form fields -->
                <input type="hidden" id="${hiddenLatId}" name="latitude">
                <input type="hidden" id="${hiddenLngId}" name="longitude">
                <input type="hidden" id="${hiddenAddressId}" name="address_text">
                <input type="hidden" id="${hiddenDistrictId}" name="district">
                <input type="hidden" id="${hiddenStateId}" name="state">
            </div>
        `;
    }

    function capture(instanceId) {
        const inst = instances[instanceId];
        if (!inst) return;

        const statusElem = document.getElementById(`${instanceId}-status`);
        const displayCard = document.getElementById(`${instanceId}-display-card`);
        const manualBox = document.getElementById(`${instanceId}-manual-box`);

        if (!navigator.geolocation) {
            if (statusElem) statusElem.innerHTML = `<span style="color: var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i> Geolocation is not supported by your browser. Please enter your address manually.</span>`;
            if (manualBox) manualBox.style.display = 'block';
            return;
        }

        if (statusElem) statusElem.innerHTML = `<span style="color: var(--primary);"><i class="fa-solid fa-spinner fa-spin"></i> Detecting location...</span>`;

        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;

                document.getElementById(inst.hiddenLatId).value = lat;
                document.getElementById(inst.hiddenLngId).value = lng;

                if (statusElem) statusElem.innerHTML = `<span style="color: var(--primary);"><i class="fa-solid fa-spinner fa-spin"></i> Reverse-geocoding address...</span>`;

                try {
                    const headers = { 'Content-Type': 'application/json' };
                    const jwtToken = localStorage.getItem('jwt_token') || localStorage.getItem('farmer_app_jwt');
                    if (jwtToken) headers['Authorization'] = 'Bearer ' + jwtToken;

                    const res = await fetch('/api/v1/geocode/reverse', {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({ latitude: lat, longitude: lng })
                    });

                    const data = await res.json();
                    if (data.success && data.address_text) {
                        document.getElementById(inst.hiddenAddressId).value = data.address_text;
                        document.getElementById(inst.hiddenDistrictId).value = data.district || '';
                        document.getElementById(inst.hiddenStateId).value = data.state || '';

                        const displayInput = document.getElementById(`${instanceId}-display`);
                        if (displayInput) displayInput.value = data.address_text;
                        if (displayCard) displayCard.style.display = 'block';

                        if (statusElem) statusElem.innerHTML = `<span style="color: #047857;"><i class="fa-solid fa-circle-check"></i> Location detected successfully!</span>`;
                    } else {
                        // Reverse geocode failed -> prompt manual fallback
                        const fallbackText = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
                        document.getElementById(inst.hiddenAddressId).value = fallbackText;
                        if (statusElem) statusElem.innerHTML = `<span style="color: #b45309;"><i class="fa-solid fa-circle-info"></i> GPS coordinates captured. Please confirm address below.</span>`;
                        if (manualBox) manualBox.style.display = 'block';
                        const manualInput = document.getElementById(inst.manualInputId);
                        if (manualInput && !manualInput.value) manualInput.value = data.error ? '' : fallbackText;
                    }
                } catch (err) {
                    console.warn('Geocoding endpoint error:', err);
                    if (statusElem) statusElem.innerHTML = `<span style="color: #b45309;"><i class="fa-solid fa-circle-info"></i> Coordinates saved. Please enter readable address below.</span>`;
                    if (manualBox) manualBox.style.display = 'block';
                }
            },
            (err) => {
                let msg = 'Unable to retrieve location.';
                if (err.code === err.PERMISSION_DENIED) {
                    msg = 'Location permission denied. Please type your address manually below.';
                } else if (err.code === err.POSITION_UNAVAILABLE) {
                    msg = 'Position unavailable. Please type your address manually below.';
                } else if (err.code === err.TIMEOUT) {
                    msg = 'Location detection timed out. Please type your address manually below.';
                }

                if (statusElem) statusElem.innerHTML = `<span style="color: var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i> ${msg}</span>`;
                if (manualBox) manualBox.style.display = 'block';
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    function toggleManual(instanceId) {
        const inst = instances[instanceId];
        if (!inst) return;
        const manualBox = document.getElementById(`${instanceId}-manual-box`);
        if (manualBox) {
            manualBox.style.display = (manualBox.style.display === 'none' || !manualBox.style.display) ? 'block' : 'none';
        }
    }

    function onManualInput(instanceId) {
        const inst = instances[instanceId];
        if (!inst) return;
        const val = document.getElementById(inst.manualInputId).value.trim();
        document.getElementById(inst.hiddenAddressId).value = val;
    }

    function getData(instanceId) {
        const inst = instances[instanceId];
        if (!inst) return { isValid: false };

        const lat = document.getElementById(inst.hiddenLatId).value;
        const lng = document.getElementById(inst.hiddenLngId).value;
        const address = document.getElementById(inst.hiddenAddressId).value || document.getElementById(inst.manualInputId).value;
        const district = document.getElementById(inst.hiddenDistrictId).value;
        const state = document.getElementById(inst.hiddenStateId).value;

        const isValid = (address && address.trim().length > 0);
        return {
            isValid,
            latitude: lat ? parseFloat(lat) : null,
            longitude: lng ? parseFloat(lng) : null,
            address_text: address ? address.trim() : '',
            district: district ? district.trim() : null,
            state: state ? state.trim() : null
        };
    }

    return {
        init,
        capture,
        toggleManual,
        onManualInput,
        getData
    };
})();
