// ============================================================================
// Analytics & Consent Integration
// JARVIS Research OS
// ============================================================================

const ANALYTICS_CONFIG = {
    googleAnalytics: {
        measurementId: "G-XXXXXXXXXX", // Replace with your GA4 Measurement ID
        enabled: false // Set true after providing a real Measurement ID
    },
    googleTagManager: {
        containerId: "GTM-XXXXXXX", // Replace with your GTM Container ID
        enabled: false
    },
    hotjar: {
        siteId: "XXXXXXX", // Replace with your Hotjar Site ID
        enabled: false
    },
    microsoftClarity: {
        projectId: "XXXXXXXXXX", // Replace with your Clarity Project ID
        enabled: false
    }
};

const CONSENT_STORAGE_KEY = "jarvis_cookie_consent";
const LEGACY_CONSENT_STORAGE_KEY = "cookie_consent";
const CONSENT_ACCEPTED = "accepted";
const CONSENT_REJECTED = "rejected";

function hasRealId(value, placeholder) {
    return Boolean(value) && value !== placeholder;
}

function getConsentState() {
    try {
        const state = localStorage.getItem(CONSENT_STORAGE_KEY);
        if (state === CONSENT_ACCEPTED || state === CONSENT_REJECTED) {
            return state;
        }

        const legacy = localStorage.getItem(LEGACY_CONSENT_STORAGE_KEY);
        if (legacy === "true") {
            return CONSENT_ACCEPTED;
        }
        if (legacy === "false") {
            return CONSENT_REJECTED;
        }
    } catch (_err) {
        // ignore storage access errors (private mode etc.)
    }
    return "";
}

function setConsentState(state) {
    try {
        localStorage.setItem(CONSENT_STORAGE_KEY, state);
        localStorage.setItem(
            LEGACY_CONSENT_STORAGE_KEY,
            state === CONSENT_ACCEPTED ? "true" : "false"
        );
    } catch (_err) {
        // ignore storage access errors
    }
}

class GoogleAnalytics {
    constructor(measurementId) {
        this.measurementId = measurementId;
        this.initialized = false;
    }

    init() {
        if (!hasRealId(this.measurementId, "G-XXXXXXXXXX")) {
            return;
        }
        if (this.initialized) {
            return;
        }

        const script = document.createElement("script");
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${this.measurementId}`;
        document.head.appendChild(script);

        window.dataLayer = window.dataLayer || [];
        window.gtag = function gtag() {
            window.dataLayer.push(arguments);
        };

        window.gtag("js", new Date());
        window.gtag("config", this.measurementId, {
            page_path: window.location.pathname,
            send_page_view: true,
            anonymize_ip: true
        });

        this.initialized = true;
    }

    trackEvent(eventName, eventParams = {}) {
        if (!this.initialized || typeof window.gtag !== "function") {
            return;
        }
        window.gtag("event", eventName, eventParams);
    }

    trackPageView(pagePath) {
        if (!this.initialized || typeof window.gtag !== "function") {
            return;
        }
        window.gtag("config", this.measurementId, { page_path: pagePath });
    }
}

class GoogleTagManager {
    constructor(containerId) {
        this.containerId = containerId;
        this.initialized = false;
    }

    init() {
        if (!hasRealId(this.containerId, "GTM-XXXXXXX")) {
            return;
        }
        if (this.initialized) {
            return;
        }

        (function loadGtm(w, d, s, l, i) {
            w[l] = w[l] || [];
            w[l].push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
            const firstScript = d.getElementsByTagName(s)[0];
            const tag = d.createElement(s);
            const layer = l !== "dataLayer" ? `&l=${l}` : "";
            tag.async = true;
            tag.src = `https://www.googletagmanager.com/gtm.js?id=${i}${layer}`;
            firstScript.parentNode.insertBefore(tag, firstScript);
        })(window, document, "script", "dataLayer", this.containerId);

        this.initialized = true;
    }

    pushEvent(eventName, eventData = {}) {
        if (!this.initialized) {
            return;
        }
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({
            event: eventName,
            ...eventData
        });
    }
}

class Hotjar {
    constructor(siteId) {
        this.siteId = siteId;
        this.initialized = false;
    }

    init() {
        if (!hasRealId(this.siteId, "XXXXXXX")) {
            return;
        }
        if (this.initialized) {
            return;
        }

        (function loadHotjar(h, o, t, j, a, r, siteId) {
            h.hj = h.hj || function hj() {
                (h.hj.q = h.hj.q || []).push(arguments);
            };
            h._hjSettings = { hjid: siteId, hjsv: 6 };
            a = o.getElementsByTagName("head")[0];
            r = o.createElement("script");
            r.async = 1;
            r.src = `${t}${h._hjSettings.hjid}${j}${h._hjSettings.hjsv}`;
            a.appendChild(r);
        })(window, document, "https://static.hotjar.com/c/hotjar-", ".js?sv=", null, null, this.siteId);

        this.initialized = true;
    }

    triggerEvent(eventName) {
        if (this.initialized && typeof window.hj === "function") {
            window.hj("event", eventName);
        }
    }
}

class MicrosoftClarity {
    constructor(projectId) {
        this.projectId = projectId;
        this.initialized = false;
    }

    init() {
        if (!hasRealId(this.projectId, "XXXXXXXXXX")) {
            return;
        }
        if (this.initialized) {
            return;
        }

        (function loadClarity(c, l, a, r, i, t, y) {
            c[a] = c[a] || function clarity() {
                (c[a].q = c[a].q || []).push(arguments);
            };
            t = l.createElement(r);
            t.async = 1;
            t.src = `https://www.clarity.ms/tag/${i}`;
            y = l.getElementsByTagName(r)[0];
            y.parentNode.insertBefore(t, y);
        })(window, document, "clarity", "script", this.projectId);

        this.initialized = true;
    }
}

class AnalyticsManager {
    constructor(config) {
        this.config = config;
        this.ga = null;
        this.gtm = null;
        this.hotjar = null;
        this.clarity = null;
        this.initialized = false;
    }

    init() {
        if (this.initialized) {
            return;
        }

        if (this.config.googleAnalytics.enabled) {
            this.ga = new GoogleAnalytics(this.config.googleAnalytics.measurementId);
            this.ga.init();
        }
        if (this.config.googleTagManager.enabled) {
            this.gtm = new GoogleTagManager(this.config.googleTagManager.containerId);
            this.gtm.init();
        }
        if (this.config.hotjar.enabled) {
            this.hotjar = new Hotjar(this.config.hotjar.siteId);
            this.hotjar.init();
        }
        if (this.config.microsoftClarity.enabled) {
            this.clarity = new MicrosoftClarity(this.config.microsoftClarity.projectId);
            this.clarity.init();
        }

        this.setupAutomaticTracking();
        this.initialized = true;
    }

    setupAutomaticTracking() {
        document.querySelectorAll(".btn, .cta-button, button[class*='btn']").forEach((button) => {
            button.addEventListener("click", () => {
                this.trackEvent("button_click", {
                    button_text: button.textContent.trim(),
                    button_class: button.className
                });
            });
        });

        document.querySelectorAll("form").forEach((form) => {
            form.addEventListener("submit", () => {
                this.trackEvent("form_submit", { form_id: form.id || "unnamed_form" });
            });
        });

        document.querySelectorAll("a[href^='http']").forEach((link) => {
            if (!link.href.includes(window.location.hostname)) {
                link.addEventListener("click", () => {
                    this.trackEvent("outbound_click", {
                        link_url: link.href,
                        link_text: link.textContent.trim()
                    });
                });
            }
        });

        let maxScroll = 0;
        const milestones = [25, 50, 75, 90, 100];
        const trackedMilestones = new Set();
        window.addEventListener("scroll", () => {
            const denominator = document.documentElement.scrollHeight - window.innerHeight;
            if (denominator <= 0) {
                return;
            }
            const scrollPercent = Math.round((window.scrollY / denominator) * 100);
            if (scrollPercent <= maxScroll) {
                return;
            }
            maxScroll = scrollPercent;
            milestones.forEach((milestone) => {
                if (scrollPercent >= milestone && !trackedMilestones.has(milestone)) {
                    trackedMilestones.add(milestone);
                    this.trackEvent("scroll_depth", { percent: milestone });
                }
            });
        });

        const startedAt = Date.now();
        window.addEventListener("beforeunload", () => {
            const seconds = Math.round((Date.now() - startedAt) / 1000);
            this.trackEvent("time_on_page", { seconds });
        });
    }

    trackEvent(eventName, eventParams = {}) {
        const payload = {
            ...eventParams,
            page_path: window.location.pathname,
            page_title: document.title,
            timestamp: new Date().toISOString()
        };

        if (this.ga) {
            this.ga.trackEvent(eventName, payload);
        }
        if (this.gtm) {
            this.gtm.pushEvent(eventName, payload);
        }
        if (this.hotjar && eventName !== "scroll_depth") {
            this.hotjar.triggerEvent(eventName);
        }
    }

    trackPageView(pagePath = window.location.pathname) {
        if (this.ga) {
            this.ga.trackPageView(pagePath);
        }
    }
}

let analytics = null;

function initializeAnalyticsIfConsented() {
    if (getConsentState() !== CONSENT_ACCEPTED) {
        return;
    }
    if (analytics && analytics.initialized) {
        return;
    }
    analytics = new AnalyticsManager(ANALYTICS_CONFIG);
    analytics.init();
    window.JARVIS_Analytics = analytics;
}

class CookieConsent {
    constructor() {
        this.state = getConsentState();
    }

    renderIfNeeded() {
        if (this.state === CONSENT_ACCEPTED || this.state === CONSENT_REJECTED) {
            return;
        }
        if (document.getElementById("cookie-consent-banner")) {
            return;
        }

        const banner = document.createElement("div");
        banner.id = "cookie-consent-banner";
        banner.innerHTML = `
            <div style="position:fixed;bottom:0;left:0;right:0;background:rgba(15,23,42,0.96);padding:20px;z-index:10000;border-top:1px solid rgba(255,255,255,0.12);backdrop-filter:blur(10px);">
              <div style="max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
                <p style="margin:0;color:#F1F5F9;font-size:14px;line-height:1.6;">
                  このサイトは利用状況の改善のために Analytics（GA4 / Hotjar など）を使用します。
                </p>
                <div style="display:flex;gap:10px;">
                  <button id="cookie-accept" style="padding:10px 16px;background:linear-gradient(135deg,#6366F1,#8B5CF6);color:#fff;border:0;border-radius:8px;cursor:pointer;font-weight:600;">同意して続行</button>
                  <button id="cookie-reject" style="padding:10px 16px;background:rgba(255,255,255,0.08);color:#fff;border:1px solid rgba(255,255,255,0.2);border-radius:8px;cursor:pointer;">拒否</button>
                </div>
              </div>
            </div>
        `;
        document.body.appendChild(banner);

        const acceptButton = document.getElementById("cookie-accept");
        const rejectButton = document.getElementById("cookie-reject");

        if (acceptButton) {
            acceptButton.addEventListener("click", () => {
                setConsentState(CONSENT_ACCEPTED);
                initializeAnalyticsIfConsented();
                banner.remove();
            });
        }

        if (rejectButton) {
            rejectButton.addEventListener("click", () => {
                setConsentState(CONSENT_REJECTED);
                window.JARVIS_Analytics = null;
                banner.remove();
            });
        }
    }
}

window.trackCustomEvent = (eventName, params) => {
    if (analytics && analytics.initialized) {
        analytics.trackEvent(eventName, params);
    }
};

document.addEventListener("DOMContentLoaded", () => {
    window.JARVIS_Analytics = null;
    initializeAnalyticsIfConsented();
    const cookieConsent = new CookieConsent();
    cookieConsent.renderIfNeeded();
});
