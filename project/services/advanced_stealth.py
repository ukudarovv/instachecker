"""
🛡️ Advanced Fingerprint Spoofing & Stealth Mode

Comprehensive browser fingerprint protection including:
- Canvas fingerprinting protection
- WebGL advanced spoofing
- Audio context fingerprinting
- Battery API masking
- Timezone/language consistency
- Hardware fingerprint randomization
"""

from typing import Dict, Optional, List
import random


class AdvancedStealthMode:
    """
    Advanced stealth mode for browser automation
    
    Protects against:
    - Canvas fingerprinting
    - WebGL fingerprinting  
    - Audio context fingerprinting
    - Battery API detection
    - Hardware fingerprinting
    - Automation detection
    """
    
    def __init__(self):
        """Initialize stealth mode with random fingerprint profile"""
        self.fingerprint_profile = self._generate_fingerprint_profile()
        
        print(f"[STEALTH] 🛡️ Generated fingerprint profile")
    
    def _generate_fingerprint_profile(self) -> Dict:
        """Generate random but consistent fingerprint profile"""
        
        # Device profiles (realistic combinations)
        devices = [
            {
                'name': 'MacBook Pro 16" 2021',
                'platform': 'MacIntel',
                'hardware_concurrency': 10,
                'device_memory': 16,
                'max_touch_points': 0,
                'webgl_vendor': 'Intel Inc.',
                'webgl_renderer': 'Intel(R) Iris(TM) Plus Graphics 655',
                'screen': {'width': 3456, 'height': 2234, 'colorDepth': 24}
            },
            {
                'name': 'MacBook Air M1',
                'platform': 'MacIntel',
                'hardware_concurrency': 8,
                'device_memory': 8,
                'max_touch_points': 0,
                'webgl_vendor': 'Apple Inc.',
                'webgl_renderer': 'Apple M1',
                'screen': {'width': 2560, 'height': 1600, 'colorDepth': 24}
            },
            {
                'name': 'Windows Desktop i7',
                'platform': 'Win32',
                'hardware_concurrency': 12,
                'device_memory': 32,
                'max_touch_points': 0,
                'webgl_vendor': 'Google Inc. (NVIDIA)',
                'webgl_renderer': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)',
                'screen': {'width': 2560, 'height': 1440, 'colorDepth': 24}
            },
            {
                'name': 'Windows Laptop i5',
                'platform': 'Win32',
                'hardware_concurrency': 8,
                'device_memory': 16,
                'max_touch_points': 0,
                'webgl_vendor': 'Google Inc. (Intel)',
                'webgl_renderer': 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)',
                'screen': {'width': 1920, 'height': 1080, 'colorDepth': 24}
            }
        ]
        
        profile = random.choice(devices)
        
        # Add randomized properties
        profile['timezone'] = random.choice([
            'America/New_York', 'America/Los_Angeles', 'America/Chicago',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin',
            'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'
        ])
        
        profile['language'] = random.choice([
            'en-US', 'en-GB', 'de-DE', 'fr-FR', 'es-ES', 'ja-JP', 'zh-CN'
        ])
        
        profile['languages'] = [profile['language'], profile['language'].split('-')[0]]
        
        # Canvas noise seed (for consistent noise)
        profile['canvas_noise_seed'] = random.random()
        
        # Audio noise parameters
        profile['audio_noise_factor'] = random.uniform(0.0001, 0.001)
        
        return profile
    
    def get_init_scripts(self) -> List[str]:
        """
        Get all stealth init scripts
        
        Returns:
            List of JavaScript code strings to inject
        """
        scripts = [
            self._get_webdriver_removal_script(),
            self._get_canvas_protection_script(),
            self._get_webgl_spoofing_script(),
            self._get_audio_protection_script(),
            self._get_battery_api_masking_script(),
            self._get_permissions_masking_script(),
            self._get_plugins_spoofing_script(),
            self._get_hardware_spoofing_script(),
            self._get_timezone_language_script(),
            self._get_chrome_object_script()
        ]
        
        return scripts
    
    def _get_webdriver_removal_script(self) -> str:
        """Remove webdriver property"""
        return """
        () => {
            // Remove webdriver property
            delete Object.getPrototypeOf(navigator).webdriver;
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Remove automation detection
            window.navigator.chrome = {
                runtime: {},
            };
            
            // Override toString to hide proxy
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === navigator.webdriver) {
                    return 'undefined';
                }
                return originalToString.call(this);
            };
        }
        """
    
    def _get_canvas_protection_script(self) -> str:
        """Protect against canvas fingerprinting"""
        noise_seed = self.fingerprint_profile['canvas_noise_seed']
        
        return f"""
        () => {{
            const noiseSeed = {noise_seed};
            
            // Canvas noise injection
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            // Add subtle noise to canvas
            function addCanvasNoise(imageData) {{
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {{
                    // Add very subtle random noise (based on seed)
                    const noise = (Math.sin(noiseSeed * i) * 2 - 1) * 1;
                    data[i] = Math.min(255, Math.max(0, data[i] + noise));
                    data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise));
                    data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise));
                }}
                return imageData;
            }}
            
            HTMLCanvasElement.prototype.toDataURL = function() {{
                const context = this.getContext('2d');
                if (context) {{
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    addCanvasNoise(imageData);
                    context.putImageData(imageData, 0, 0);
                }}
                return originalToDataURL.apply(this, arguments);
            }};
            
            CanvasRenderingContext2D.prototype.getImageData = function() {{
                const imageData = originalGetImageData.apply(this, arguments);
                return addCanvasNoise(imageData);
            }};
            
            // Detect and block known fingerprinting canvases
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function() {{
                const context = originalGetContext.apply(this, arguments);
                
                // Detect fingerprinting attempts (common sizes)
                if (this.width === 280 && this.height === 60) {{
                    // Instagram fingerprinting canvas
                    console.log('[Stealth] Blocked fingerprinting canvas');
                    return null;
                }}
                
                return context;
            }};
        }}
        """
    
    def _get_webgl_spoofing_script(self) -> str:
        """Advanced WebGL fingerprint spoofing"""
        vendor = self.fingerprint_profile['webgl_vendor']
        renderer = self.fingerprint_profile['webgl_renderer']
        
        return f"""
        () => {{
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                // Vendor
                if (parameter === 37445) {{
                    return '{vendor}';
                }}
                // Renderer
                if (parameter === 37446) {{
                    return '{renderer}';
                }}
                // Max vertex attributes
                if (parameter === 34921) {{
                    return 16;
                }}
                // Max texture size
                if (parameter === 3379) {{
                    return 16384;
                }}
                // Max viewport dims
                if (parameter === 3386) {{
                    return new Int32Array([16384, 16384]);
                }}
                
                return getParameter.call(this, parameter);
            }};
            
            // WebGL2 support
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{vendor}';
                if (parameter === 37446) return '{renderer}';
                if (parameter === 34921) return 16;
                if (parameter === 3379) return 16384;
                if (parameter === 3386) return new Int32Array([16384, 16384]);
                
                return getParameter2.call(this, parameter);
            }};
        }}
        """
    
    def _get_audio_protection_script(self) -> str:
        """Protect against audio context fingerprinting"""
        noise_factor = self.fingerprint_profile['audio_noise_factor']
        
        return f"""
        () => {{
            const noiseFactor = {noise_factor};
            
            // AudioContext fingerprinting protection
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            
            if (AudioContext) {{
                const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
                
                AudioContext.prototype.createAnalyser = function() {{
                    const analyser = originalCreateAnalyser.apply(this, arguments);
                    
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    
                    analyser.getFloatFrequencyData = function(array) {{
                        originalGetFloatFrequencyData.apply(this, arguments);
                        
                        // Add subtle noise to audio fingerprint
                        for (let i = 0; i < array.length; i++) {{
                            array[i] += (Math.random() - 0.5) * noiseFactor;
                        }}
                        
                        return array;
                    }};
                    
                    return analyser;
                }};
                
                // Protect OfflineAudioContext
                const OfflineAudioContext = window.OfflineAudioContext || window.webkitOfflineAudioContext;
                
                if (OfflineAudioContext) {{
                    const originalStartRendering = OfflineAudioContext.prototype.startRendering;
                    
                    OfflineAudioContext.prototype.startRendering = function() {{
                        console.log('[Stealth] Audio fingerprinting detected');
                        return originalStartRendering.apply(this, arguments);
                    }};
                }}
            }}
        }}
        """
    
    def _get_battery_api_masking_script(self) -> str:
        """Mask Battery API (used for fingerprinting)"""
        return """
        () => {
            // Remove Battery API
            if ('getBattery' in navigator) {
                delete navigator.getBattery;
            }
            
            Object.defineProperty(navigator, 'getBattery', {
                get: () => undefined,
                configurable: true
            });
        }
        """
    
    def _get_permissions_masking_script(self) -> str:
        """Mask permissions query"""
        return """
        () => {
            const originalQuery = window.navigator.permissions.query;
            
            window.navigator.permissions.query = (parameters) => {
                // Return denied for automation-detecting permissions
                if (parameters.name === 'notifications') {
                    return Promise.resolve({
                        state: Notification.permission,
                        onchange: null
                    });
                }
                
                return originalQuery(parameters);
            };
        }
        """
    
    def _get_plugins_spoofing_script(self) -> str:
        """Spoof plugins array"""
        return """
        () => {
            // Spoof plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {
                            name: 'Chrome PDF Plugin',
                            filename: 'internal-pdf-viewer',
                            description: 'Portable Document Format'
                        },
                        {
                            name: 'Chrome PDF Viewer',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            description: ''
                        },
                        {
                            name: 'Native Client',
                            filename: 'internal-nacl-plugin',
                            description: ''
                        }
                    ];
                },
                configurable: true
            });
        }
        """
    
    def _get_hardware_spoofing_script(self) -> str:
        """Spoof hardware properties"""
        concurrency = self.fingerprint_profile['hardware_concurrency']
        memory = self.fingerprint_profile['device_memory']
        max_touch = self.fingerprint_profile['max_touch_points']
        platform = self.fingerprint_profile['platform']
        
        return f"""
        () => {{
            // Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {concurrency},
                configurable: true
            }});
            
            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {memory},
                configurable: true
            }});
            
            // Max touch points
            Object.defineProperty(navigator, 'maxTouchPoints', {{
                get: () => {max_touch},
                configurable: true
            }});
            
            // Platform
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{platform}',
                configurable: true
            }});
        }}
        """
    
    def _get_timezone_language_script(self) -> str:
        """Consistent timezone and language"""
        timezone = self.fingerprint_profile['timezone']
        language = self.fingerprint_profile['language']
        languages = self.fingerprint_profile['languages']
        
        return f"""
        () => {{
            // Timezone spoofing
            const originalDateTimeFormat = Intl.DateTimeFormat;
            
            Intl.DateTimeFormat = function(...args) {{
                if (args.length === 0 || (args[0] === undefined && args[1] === undefined)) {{
                    args[0] = '{language}';
                }}
                return new originalDateTimeFormat(...args);
            }};
            
            Intl.DateTimeFormat.prototype = originalDateTimeFormat.prototype;
            
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    const options = originalDateTimeFormat.prototype.resolvedOptions.call(this);
                    options.timeZone = '{timezone}';
                    return options;
                }}
            }});
            
            // Language spoofing
            Object.defineProperty(navigator, 'language', {{
                get: () => '{language}',
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => {languages},
                configurable: true
            }});
        }}
        """
    
    def _get_chrome_object_script(self) -> str:
        """Add chrome object for Chromium browsers"""
        return """
        () => {
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            }
        }
        """
    
    async def apply_to_page(self, page):
        """
        Apply all stealth scripts to Playwright page
        
        Args:
            page: Playwright page object
        """
        print(f"[STEALTH] 🛡️ Applying advanced stealth mode...")
        
        scripts = self.get_init_scripts()
        
        for i, script in enumerate(scripts, 1):
            try:
                await page.add_init_script(script)
            except Exception as e:
                print(f"[STEALTH] ⚠️ Error applying script {i}: {e}")
        
        print(f"[STEALTH] ✅ Applied {len(scripts)} stealth scripts")
    
    def get_profile_info(self) -> Dict:
        """Get fingerprint profile info"""
        return {
            'device': self.fingerprint_profile['name'],
            'platform': self.fingerprint_profile['platform'],
            'hardware_concurrency': self.fingerprint_profile['hardware_concurrency'],
            'device_memory': self.fingerprint_profile['device_memory'],
            'webgl_vendor': self.fingerprint_profile['webgl_vendor'],
            'timezone': self.fingerprint_profile['timezone'],
            'language': self.fingerprint_profile['language']
        }


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

async def apply_advanced_stealth(page) -> AdvancedStealthMode:
    """
    Apply advanced stealth mode to page (convenience function)
    
    Args:
        page: Playwright page object
        
    Returns:
        AdvancedStealthMode instance
    """
    stealth = AdvancedStealthMode()
    await stealth.apply_to_page(page)
    return stealth




