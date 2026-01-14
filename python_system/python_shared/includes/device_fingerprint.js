/**
 * Advanced Device Fingerprinting & User Intelligence
 * Creates unique device ID and tracks user behavior patterns
 */

class DeviceFingerprint {
    constructor() {
        this.deviceId = null;
        this.profile = null;
        this.initialized = false;
    }

    /**
     * Generate unique device fingerprint
     */
    async generateFingerprint() {
        const components = [];

        // Screen properties
        components.push(window.screen.width);
        components.push(window.screen.height);
        components.push(window.screen.colorDepth);
        components.push(window.screen.pixelDepth);

        // Browser properties
        components.push(navigator.userAgent);
        components.push(navigator.language);
        components.push(navigator.languages ? navigator.languages.join(',') : '');
        components.push(navigator.platform);
        components.push(navigator.hardwareConcurrency || 0);
        components.push(navigator.deviceMemory || 0);

        // Timezone
        components.push(Intl.DateTimeFormat().resolvedOptions().timeZone);
        components.push(new Date().getTimezoneOffset());

        // Canvas fingerprint
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('AdSphere', 2, 2);
        components.push(canvas.toDataURL());

        // WebGL fingerprint
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (debugInfo) {
                components.push(gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL));
                components.push(gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL));
            }
        }

        // Audio fingerprint
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const analyser = audioContext.createAnalyser();
            const gainNode = audioContext.createGain();

            oscillator.connect(analyser);
            analyser.connect(gainNode);
            gainNode.connect(audioContext.destination);

            components.push(audioContext.sampleRate);
            audioContext.close();
        } catch (e) {
            components.push('audio-unavailable');
        }

        // Plugins (deprecated but still useful)
        if (navigator.plugins) {
            const plugins = Array.from(navigator.plugins).map(p => p.name).join(',');
            components.push(plugins);
        }

        // Touch support
        components.push(navigator.maxTouchPoints || 0);
        components.push('ontouchstart' in window);

        // Combine all components and hash
        const fingerprint = components.join('|||');
        this.deviceId = await this.hashString(fingerprint);

        return this.deviceId;
    }

    /**
     * Hash string using SHA-256
     */
    async hashString(str) {
        const encoder = new TextEncoder();
        const data = encoder.encode(str);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    /**
     * Get device information
     */
    getDeviceInfo() {
        return {
            device_type: this.getDeviceType(),
            browser: this.getBrowserInfo(),
            os: this.getOS(),
            screen_size: `${window.screen.width}x${window.screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };
    }

    getDeviceType() {
        const ua = navigator.userAgent;
        if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
            return 'tablet';
        }
        if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
            return 'mobile';
        }
        return 'desktop';
    }

    getBrowserInfo() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';

        if (ua.includes('Firefox/')) browser = 'Firefox';
        else if (ua.includes('Chrome/') && !ua.includes('Edge')) browser = 'Chrome';
        else if (ua.includes('Safari/') && !ua.includes('Chrome')) browser = 'Safari';
        else if (ua.includes('Edge/')) browser = 'Edge';
        else if (ua.includes('MSIE') || ua.includes('Trident/')) browser = 'IE';

        return browser;
    }

    getOS() {
        const ua = navigator.userAgent;

        if (ua.includes('Win')) return 'Windows';
        if (ua.includes('Mac')) return 'MacOS';
        if (ua.includes('Linux')) return 'Linux';
        if (ua.includes('Android')) return 'Android';
        if (ua.includes('iOS') || ua.includes('iPhone') || ua.includes('iPad')) return 'iOS';

        return 'Unknown';
    }

    /**
     * Initialize and load user profile
     */
    async init() {
        if (this.initialized) return this.profile;

        // Generate device ID
        await this.generateFingerprint();

        // Get or create profile
        try {
            const response = await fetch('/app/api/user_profiling.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'get_profile',
                    device_id: this.deviceId,
                    ...this.getDeviceInfo()
                })
            });

            const data = await response.json();
            if (data.success) {
                this.profile = data.profile;
                this.initialized = true;

                // Store device ID in localStorage for quick access
                localStorage.setItem('adsphere_device_id', this.deviceId);

                return this.profile;
            }
        } catch (e) {
            console.error('Failed to initialize device profile:', e);
        }

        return null;
    }

    /**
     * Update user profile with new preferences
     */
    async updateProfile(preferences) {
        if (!this.deviceId) return false;

        try {
            const response = await fetch('/app/api/user_profiling.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'update_profile',
                    device_id: this.deviceId,
                    preferences: preferences
                })
            });

            const data = await response.json();
            if (data.success) {
                this.profile = data.profile;
                return true;
            }
        } catch (e) {
            console.error('Failed to update profile:', e);
        }

        return false;
    }

    /**
     * Get personalized ad recommendations
     */
    async getRecommendations() {
        if (!this.deviceId) {
            await this.init();
        }

        try {
            const response = await fetch('/app/api/user_profiling.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'get_recommendations',
                    device_id: this.deviceId
                })
            });

            const data = await response.json();
            if (data.success) {
                return data.recommendations;
            }
        } catch (e) {
            console.error('Failed to get recommendations:', e);
        }

        return [];
    }

    /**
     * Track ad interaction
     */
    async trackInteraction(adId, interactionType, metadata = {}) {
        const preferences = {
            viewed_ads: [adId]
        };

        if (interactionType === 'like') {
            preferences.liked_ads = [adId];
        } else if (interactionType === 'dislike') {
            preferences.disliked_ads = [adId];
        } else if (interactionType === 'favorite') {
            preferences.favorite_ads = [adId];
        } else if (interactionType === 'contact') {
            preferences.contacted_ads = [adId];
        } else if (interactionType === 'time_spent') {
            preferences.time_spent = metadata.seconds || 0;
        }

        await this.updateProfile(preferences);
    }

    /**
     * Track category preference
     */
    async trackCategoryInteraction(category, isLike) {
        const preferences = isLike
            ? { liked_categories: [category] }
            : { disliked_categories: [category] };

        await this.updateProfile(preferences);
    }
}

// Global instance
window.deviceFingerprint = new DeviceFingerprint();

