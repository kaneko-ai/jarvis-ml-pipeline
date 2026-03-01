// ==========================================================================
// Particle Animation (Hero Background)
// ==========================================================================

class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 50;
        this.connections = [];
        
        this.resize();
        this.init();
        
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
    }
    
    init() {
        this.particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 2 + 1
            });
        }
    }
    
    update() {
        this.particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
        });
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw connections
        this.particles.forEach((p1, i) => {
            this.particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 150) {
                    const opacity = (1 - distance / 150) * 0.3;
                    this.ctx.strokeStyle = `rgba(99, 102, 241, ${opacity})`;
                    this.ctx.lineWidth = 1;
                    this.ctx.beginPath();
                    this.ctx.moveTo(p1.x, p1.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.stroke();
                }
            });
        });
        
        // Draw particles
        this.particles.forEach(particle => {
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(129, 140, 248, 0.8)';
            this.ctx.fill();
        });
    }
    
    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize particle system
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('particleCanvas');
    if (canvas) {
        const particleSystem = new ParticleSystem(canvas);
        particleSystem.animate();
    }
});

// ==========================================================================
// Navigation Scroll Effect
// ==========================================================================

let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
});

// ==========================================================================
// Mobile Menu
// ==========================================================================

const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const navLinks = document.querySelector('.nav-links');

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        mobileMenuBtn.classList.toggle('active');
    });
}

// ==========================================================================
// Demo Section - Tab Switching
// ==========================================================================

const tabButtons = document.querySelectorAll('.tab-btn');
const demoPanels = document.querySelectorAll('.demo-panel');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const targetTab = button.dataset.tab;
        
        // Remove active class from all tabs and panels
        tabButtons.forEach(btn => btn.classList.remove('active'));
        demoPanels.forEach(panel => panel.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding panel
        button.classList.add('active');
        document.getElementById(`${targetTab}-panel`).classList.add('active');
    });
});

// ==========================================================================
// Demo API Connectivity
// ==========================================================================

const API_STORAGE_KEY = 'jarvis_api_base_url';
const API_DEFAULT_TIMEOUT_MS = (window.JARVIS_SITE_CONFIG && window.JARVIS_SITE_CONFIG.requestTimeoutMs) || 12000;

function normalizeApiBaseUrl(value) {
    const trimmed = (value || '').trim();
    if (!trimmed) return '';
    return trimmed.replace(/\/+$/, '');
}

function resolveApiBaseUrl() {
    const stored = normalizeApiBaseUrl(localStorage.getItem(API_STORAGE_KEY));
    if (stored) return stored;

    const configValue = normalizeApiBaseUrl(
        window.JARVIS_SITE_CONFIG && window.JARVIS_SITE_CONFIG.apiBaseUrl
    );
    if (configValue) return configValue;

    return '';
}

let currentApiBaseUrl = resolveApiBaseUrl();

function isGitHubPagesHost() {
    return window.location.hostname.endsWith('github.io');
}

function getApiUrl(path) {
    if (currentApiBaseUrl) {
        return `${currentApiBaseUrl}${path}`;
    }
    return path;
}

function setApiStatus(mode, message) {
    const statusEl = document.getElementById('api-status');
    if (!statusEl) return;

    statusEl.className = 'api-connection-status';
    if (mode === 'online') statusEl.classList.add('api-connection-status--online');
    if (mode === 'testing') statusEl.classList.add('api-connection-status--testing');
    if (mode === 'offline') statusEl.classList.add('api-connection-status--offline');
    if (mode === 'mock') statusEl.classList.add('api-connection-status--mock');
    statusEl.textContent = message;
}

async function fetchJsonWithTimeout(url, options = {}, timeoutMs = API_DEFAULT_TIMEOUT_MS) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        const body = await response.json().catch(() => null);
        if (!response.ok) {
            const detail = body && body.detail ? body.detail : `HTTP ${response.status}`;
            throw new Error(detail);
        }
        return body;
    } finally {
        clearTimeout(timeoutId);
    }
}

async function pingApi() {
    if (!currentApiBaseUrl && isGitHubPagesHost()) {
        setApiStatus('mock', 'Mock mode (API URLを設定すると本番解析が動作します)');
        return false;
    }

    setApiStatus('testing', 'Checking API connection...');
    try {
        await fetchJsonWithTimeout(getApiUrl('/api/health'), { method: 'GET' }, 6000);
        setApiStatus('online', `Connected: ${currentApiBaseUrl || 'same-origin'}`);
        return true;
    } catch (error) {
        setApiStatus('offline', `API unavailable: ${error.message}`);
        return false;
    }
}

function initializeApiConfigControls() {
    const inputEl = document.getElementById('api-base-url');
    const saveButton = document.getElementById('api-save-btn');
    const testButton = document.getElementById('api-test-btn');
    if (!inputEl || !saveButton || !testButton) return;

    inputEl.value = currentApiBaseUrl;

    saveButton.addEventListener('click', async () => {
        currentApiBaseUrl = normalizeApiBaseUrl(inputEl.value);
        if (currentApiBaseUrl) {
            localStorage.setItem(API_STORAGE_KEY, currentApiBaseUrl);
        } else {
            localStorage.removeItem(API_STORAGE_KEY);
        }
        await pingApi();
    });

    testButton.addEventListener('click', async () => {
        const candidate = normalizeApiBaseUrl(inputEl.value);
        if (candidate !== currentApiBaseUrl) {
            currentApiBaseUrl = candidate;
        }
        await pingApi();
    });

    pingApi();
}

function mapQualityRating(level) {
    if (['1a', '1b', '1c'].includes(level)) return 'High';
    if (['2a', '2b', '2c'].includes(level)) return 'Moderate';
    return 'Low';
}

async function requestEvidenceFromApi(title, abstract) {
    try {
        const payload = await fetchJsonWithTimeout(
            getApiUrl('/api/demo/evidence/grade'),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, abstract })
            }
        );
        const data = payload && payload.data ? payload.data : payload;
        if (!data || !data.level) return null;
        return {
            level: data.level,
            description: data.description || 'Evidence grading result from API',
            confidence: Number(data.confidence),
            qualityRating: data.quality_rating || mapQualityRating(data.level),
            source: 'api'
        };
    } catch {
        return null;
    }
}

async function requestCitationFromApi(text) {
    try {
        const payload = await fetchJsonWithTimeout(
            getApiUrl('/api/demo/citation/analyze'),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            }
        );
        const data = payload && payload.data ? payload.data : payload;
        if (!data || !Array.isArray(data.citations)) return null;
        return {
            citations: data.citations,
            source: 'api'
        };
    } catch {
        return null;
    }
}

async function requestContradictionFromApi(claimA, claimB) {
    try {
        const payload = await fetchJsonWithTimeout(
            getApiUrl('/api/demo/contradiction/detect'),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ claim_a: claimA, claim_b: claimB })
            }
        );
        const data = payload && payload.data ? payload.data : payload;
        if (!data || typeof data.isContradictory === 'undefined') return null;
        return {
            isContradictory: Boolean(data.isContradictory),
            confidence: Number(data.confidence),
            contradictionType: data.contradictionType || 'Unknown',
            explanation: data.explanation || 'No explanation from API',
            claimA: data.claimA || claimA,
            claimB: data.claimB || claimB,
            source: 'api'
        };
    } catch {
        return null;
    }
}

// ==========================================================================
// Evidence Grading Demo
// ==========================================================================

async function runEvidenceGrading() {
    const title = document.getElementById('evidence-title').value;
    const abstract = document.getElementById('evidence-abstract').value;
    const outputElement = document.getElementById('evidence-output');
    const statusElement = document.getElementById('evidence-status');
    
    if (!title || !abstract) {
        alert('Please enter both title and abstract');
        return;
    }
    
    // Update status
    statusElement.textContent = 'Analyzing...';
    statusElement.className = 'output-status analyzing';
    
    // Show loading state
    outputElement.innerHTML = `
        <div class="placeholder-state">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" style="animation: spin 1s linear infinite;">
                <circle cx="40" cy="40" r="30" stroke="#6366F1" stroke-width="4" stroke-dasharray="160" stroke-dashoffset="80" opacity="0.3"/>
            </svg>
            <p>Analyzing evidence level...</p>
        </div>
    `;

    const apiResult = await requestEvidenceFromApi(title, abstract);
    if (apiResult) {
        displayEvidenceResult(apiResult);
        statusElement.textContent = 'Complete (API)';
        statusElement.className = 'output-status complete';
        setApiStatus('online', `Connected: ${currentApiBaseUrl || 'same-origin'}`);
        return;
    }

    const fallbackResult = analyzeEvidence(title, abstract);
    fallbackResult.source = 'mock';
    displayEvidenceResult(fallbackResult);
    statusElement.textContent = 'Complete (Fallback)';
    statusElement.className = 'output-status fallback';
    setApiStatus('mock', 'Mock mode (API呼び出しに失敗したためローカル処理を実行)');
}

function analyzeEvidence(title, abstract) {
    // Sophisticated evidence grading logic
    const text = (title + ' ' + abstract).toLowerCase();
    
    // Keywords for different evidence levels
    const rctKeywords = ['randomized', 'controlled trial', 'rct', 'double-blind', 'placebo-controlled'];
    const systematicReviewKeywords = ['systematic review', 'meta-analysis', 'cochrane'];
    const cohortKeywords = ['cohort', 'prospective', 'longitudinal'];
    const caseControlKeywords = ['case-control', 'retrospective'];
    const expertOpinionKeywords = ['expert opinion', 'consensus', 'review'];
    
    let level, description, confidence;
    
    if (systematicReviewKeywords.some(kw => text.includes(kw))) {
        level = '1a';
        description = 'Systematic Review of RCTs';
        confidence = 96.5;
    } else if (rctKeywords.some(kw => text.includes(kw))) {
        level = '1b';
        description = 'Individual RCT';
        confidence = 94.5;
    } else if (cohortKeywords.some(kw => text.includes(kw))) {
        level = '2b';
        description = 'Individual Cohort Study';
        confidence = 87.2;
    } else if (caseControlKeywords.some(kw => text.includes(kw))) {
        level = '3b';
        description = 'Individual Case-Control Study';
        confidence = 78.5;
    } else if (expertOpinionKeywords.some(kw => text.includes(kw))) {
        level = '5';
        description = 'Expert Opinion';
        confidence = 65.0;
    } else {
        level = '4';
        description = 'Case-Series or Poor Quality Study';
        confidence = 70.0;
    }
    
    return {
        level,
        description,
        confidence,
        qualityRating: mapQualityRating(level),
        source: 'mock'
    };
}

function displayEvidenceResult(result) {
    const outputElement = document.getElementById('evidence-output');
    
    outputElement.innerHTML = `
        <div class="result-container">
            <div class="result-card">
                <div class="result-header">
                    <div class="result-badge level-1a">${result.level}</div>
                    <div class="result-info">
                        <div class="result-title">Evidence Level ${result.level}</div>
                        <div class="result-description">${result.description}</div>
                    </div>
                </div>
                
                <div class="result-metrics">
                    <div class="metric-item">
                        <span class="metric-label">Confidence Score</span>
                        <span class="metric-value">${result.confidence}%</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${result.confidence}%"></div>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <span class="metric-label">Quality Rating</span>
                        <span class="metric-value">${result.qualityRating || mapQualityRating(result.level)}</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${result.level === '1a' || result.level === '1b' ? 90 : result.level === '2b' ? 70 : 50}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="result-card">
                <h4 style="margin-bottom: 12px; font-size: 0.938rem;">Evidence Hierarchy Context</h4>
                <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
                    According to the Oxford Centre for Evidence-Based Medicine (CEBM) levels, 
                    this study falls into level <strong>${result.level}</strong>. 
                    ${result.level === '1a' || result.level === '1b' 
                        ? 'This represents the highest quality of evidence with minimal risk of bias.' 
                        : result.level === '2b' 
                        ? 'This represents moderate quality evidence with some risk of bias.' 
                        : 'Consider supplementing with higher quality studies.'}
                </p>
                <p style="font-size: 0.75rem; color: var(--text-tertiary); margin-top: 10px;">
                    Source: ${result.source === 'api' ? 'Backend API' : 'Browser fallback logic'}
                </p>
            </div>
        </div>
    `;
}

// ==========================================================================
// Citation Analysis Demo
// ==========================================================================

async function runCitationAnalysis() {
    const text = document.getElementById('citation-text').value;
    const outputElement = document.getElementById('citation-output');
    const statusElement = document.getElementById('citation-status');
    
    if (!text) {
        alert('Please enter text with citations');
        return;
    }
    
    statusElement.textContent = 'Analyzing...';
    statusElement.className = 'output-status analyzing';
    
    outputElement.innerHTML = `
        <div class="placeholder-state">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" style="animation: spin 1s linear infinite;">
                <circle cx="40" cy="40" r="30" stroke="#6366F1" stroke-width="4" stroke-dasharray="160" stroke-dashoffset="80" opacity="0.3"/>
            </svg>
            <p>Extracting citation contexts...</p>
        </div>
    `;

    const apiResult = await requestCitationFromApi(text);
    if (apiResult) {
        displayCitationResult(apiResult.citations, 'api');
        statusElement.textContent = 'Complete (API)';
        statusElement.className = 'output-status complete';
        setApiStatus('online', `Connected: ${currentApiBaseUrl || 'same-origin'}`);
        return;
    }

    const citations = extractCitations(text);
    displayCitationResult(citations, 'mock');
    statusElement.textContent = 'Complete (Fallback)';
    statusElement.className = 'output-status fallback';
    setApiStatus('mock', 'Mock mode (API呼び出しに失敗したためローカル処理を実行)');
}

function extractCitations(text) {
    // Extract citations (simplified)
    const citationRegex = /\(([A-Z][a-z]+ et al\.|[A-Z][a-z]+),? (\d{4})\)/g;
    const matches = [...text.matchAll(citationRegex)];
    
    const citations = matches.map((match, index) => {
        const fullMatch = match[0];
        const author = match[1];
        const year = match[2];
        const contextStart = Math.max(0, match.index - 50);
        const contextEnd = Math.min(text.length, match.index + fullMatch.length + 50);
        const context = text.slice(contextStart, contextEnd);
        
        // Classify stance based on context
        let stance = 'Mention';
        if (context.toLowerCase().includes('support') || context.toLowerCase().includes('confirm') || context.toLowerCase().includes('align')) {
            stance = 'Support';
        } else if (context.toLowerCase().includes('question') || context.toLowerCase().includes('contrary') || context.toLowerCase().includes('however')) {
            stance = 'Contrast';
        }
        
        return {
            id: `citation-${index + 1}`,
            author,
            year,
            stance,
            context: context.trim()
        };
    });
    
    return citations;
}

function displayCitationResult(citations, source = 'mock') {
    const outputElement = document.getElementById('citation-output');
    
    if (citations.length === 0) {
        outputElement.innerHTML = `
            <div class="placeholder-state">
                <p>No citations detected. Try entering text with citations like (Smith et al., 2020)</p>
            </div>
        `;
        return;
    }
    
    const supportCount = citations.filter(c => c.stance === 'Support').length;
    const contrastCount = citations.filter(c => c.stance === 'Contrast').length;
    const mentionCount = citations.filter(c => c.stance === 'Mention').length;
    
    const citationCards = citations.map(citation => `
        <div class="result-card" style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <div>
                    <strong>${citation.author} (${citation.year})</strong>
                    <span style="display: inline-block; margin-left: 8px; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; 
                        background: ${citation.stance === 'Support' ? 'rgba(16, 185, 129, 0.2)' : citation.stance === 'Contrast' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(148, 163, 184, 0.2)'};
                        color: ${citation.stance === 'Support' ? 'var(--success)' : citation.stance === 'Contrast' ? 'var(--error)' : 'var(--text-secondary)'};">
                        ${citation.stance}
                    </span>
                </div>
            </div>
            <p style="font-size: 0.875rem; color: var(--text-secondary); font-style: italic;">
                "${citation.context}"
            </p>
        </div>
    `).join('');
    
    outputElement.innerHTML = `
        <div class="result-container">
            <div class="result-card">
                <h4 style="margin-bottom: 16px; font-size: 1rem;">Citation Network Summary</h4>
                <div class="citation-stats" style="margin-bottom: 16px;">
                    <div class="citation-item support">
                        <span class="citation-label">Support</span>
                        <span class="citation-count">${supportCount}</span>
                    </div>
                    <div class="citation-item contrast">
                        <span class="citation-label">Contrast</span>
                        <span class="citation-count">${contrastCount}</span>
                    </div>
                    <div class="citation-item" style="background: rgba(148, 163, 184, 0.1);">
                        <span class="citation-label">Mention</span>
                        <span class="citation-count" style="color: var(--text-secondary);">${mentionCount}</span>
                    </div>
                </div>
                <p style="font-size: 0.875rem; color: var(--text-secondary);">
                    Detected ${citations.length} citation(s) with stance classification
                </p>
                <p style="font-size: 0.75rem; color: var(--text-tertiary); margin-top: 8px;">
                    Source: ${source === 'api' ? 'Backend API' : 'Browser fallback logic'}
                </p>
            </div>
            
            <div style="margin-top: 16px;">
                <h4 style="margin-bottom: 12px; font-size: 0.938rem;">Citation Details</h4>
                ${citationCards}
            </div>
        </div>
    `;
}

// ==========================================================================
// Contradiction Detection Demo
// ==========================================================================

async function runContradictionDetection() {
    const claimA = document.getElementById('claim-a').value;
    const claimB = document.getElementById('claim-b').value;
    const outputElement = document.getElementById('contradiction-output');
    const statusElement = document.getElementById('contradiction-status');
    
    if (!claimA || !claimB) {
        alert('Please enter both claims');
        return;
    }
    
    statusElement.textContent = 'Analyzing...';
    statusElement.className = 'output-status analyzing';
    
    outputElement.innerHTML = `
        <div class="placeholder-state">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" style="animation: spin 1s linear infinite;">
                <circle cx="40" cy="40" r="30" stroke="#6366F1" stroke-width="4" stroke-dasharray="160" stroke-dashoffset="80" opacity="0.3"/>
            </svg>
            <p>Detecting contradictions...</p>
        </div>
    `;

    const apiResult = await requestContradictionFromApi(claimA, claimB);
    if (apiResult) {
        displayContradictionResult(apiResult);
        statusElement.textContent = 'Complete (API)';
        statusElement.className = 'output-status complete';
        setApiStatus('online', `Connected: ${currentApiBaseUrl || 'same-origin'}`);
        return;
    }

    const fallbackResult = detectContradiction(claimA, claimB);
    fallbackResult.source = 'mock';
    displayContradictionResult(fallbackResult);
    statusElement.textContent = 'Complete (Fallback)';
    statusElement.className = 'output-status fallback';
    setApiStatus('mock', 'Mock mode (API呼び出しに失敗したためローカル処理を実行)');
}

function detectContradiction(claimA, claimB) {
    const textA = claimA.toLowerCase();
    const textB = claimB.toLowerCase();
    
    // Check for negation patterns
    const negationWords = ['not', 'no', 'never', 'decrease', 'reduce', 'lower'];
    const positiveWords = ['increase', 'improve', 'enhance', 'higher', 'significant'];
    
    const hasNegationA = negationWords.some(word => textA.includes(word));
    const hasNegationB = negationWords.some(word => textB.includes(word));
    const hasPositiveA = positiveWords.some(word => textA.includes(word));
    const hasPositiveB = positiveWords.some(word => textB.includes(word));
    
    // Extract p-values and effect sizes
    const pValueRegex = /p\s*[<>=]\s*([0-9.]+)/i;
    const pValueA = claimA.match(pValueRegex);
    const pValueB = claimB.match(pValueRegex);
    
    let isContradictory = false;
    let confidence = 0;
    let contradictionType = 'None';
    let explanation = '';
    
    // Semantic contradiction (opposite meanings)
    if ((hasPositiveA && hasNegationB) || (hasNegationA && hasPositiveB)) {
        isContradictory = true;
        confidence = 88.5;
        contradictionType = 'Semantic';
        explanation = 'The claims express opposite directions of effect (increase vs. decrease).';
    }
    
    // Statistical contradiction (conflicting significance)
    if (pValueA && pValueB) {
        const pA = parseFloat(pValueA[1]);
        const pB = parseFloat(pValueB[1]);
        
        if ((pA < 0.05 && pB >= 0.05) || (pA >= 0.05 && pB < 0.05)) {
            isContradictory = true;
            confidence = 92.3;
            contradictionType = 'Statistical';
            explanation = 'One study reports statistically significant results while the other does not.';
        }
    }
    
    if (!isContradictory) {
        confidence = 15.2;
        explanation = 'No significant contradictions detected between the claims.';
    }
    
    return {
        isContradictory,
        confidence,
        contradictionType,
        explanation,
        claimA,
        claimB,
        source: 'mock'
    };
}

function displayContradictionResult(result) {
    const outputElement = document.getElementById('contradiction-output');
    
    outputElement.innerHTML = `
        <div class="result-container">
            <div class="result-card">
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                    <div style="font-size: 3rem;">
                        ${result.isContradictory ? '⚠️' : '✅'}
                    </div>
                    <div>
                        <h3 style="font-size: 1.25rem; margin-bottom: 4px;">
                            ${result.isContradictory ? 'Contradiction Detected' : 'No Contradiction'}
                        </h3>
                        <p style="color: var(--text-secondary); font-size: 0.875rem;">
                            ${result.contradictionType} Analysis
                        </p>
                    </div>
                </div>
                
                <div class="result-metrics">
                    <div class="metric-item">
                        <span class="metric-label">Confidence Score</span>
                        <span class="metric-value">${result.confidence}%</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${result.confidence}%; 
                                background: ${result.isContradictory ? 'linear-gradient(90deg, var(--error), var(--warning))' : 'linear-gradient(90deg, var(--success), var(--accent-cyan))'};">
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <span class="metric-label">Contradiction Type</span>
                        <span class="metric-value" style="font-size: 1rem;">${result.contradictionType}</span>
                    </div>
                </div>
            </div>
            
            <div class="result-card">
                <h4 style="margin-bottom: 12px; font-size: 0.938rem;">Analysis Explanation</h4>
                <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px;">
                    ${result.explanation}
                </p>
                <p style="font-size: 0.75rem; color: var(--text-tertiary); margin-bottom: 12px;">
                    Source: ${result.source === 'api' ? 'Backend API' : 'Browser fallback logic'}
                </p>
                
                <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-bottom: 4px;">Claim A</div>
                    <p style="font-size: 0.875rem; color: var(--text-secondary);">${result.claimA}</p>
                </div>
                
                <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 8px;">
                    <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-bottom: 4px;">Claim B</div>
                    <p style="font-size: 0.875rem; color: var(--text-secondary);">${result.claimB}</p>
                </div>
            </div>
            
            ${result.isContradictory ? `
                <div class="result-card" style="border-left: 3px solid var(--warning);">
                    <h4 style="margin-bottom: 8px; font-size: 0.938rem; color: var(--warning);">⚠️ Recommendation</h4>
                    <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
                        Further investigation is recommended. Consider examining:
                    </p>
                    <ul style="margin-top: 8px; padding-left: 20px; font-size: 0.875rem; color: var(--text-secondary); line-height: 1.8;">
                        <li>Study methodologies and sample sizes</li>
                        <li>Publication dates and context</li>
                        <li>Potential confounding variables</li>
                        <li>Statistical power and effect sizes</li>
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// ==========================================================================
// Smooth Scroll Utility
// ==========================================================================

function scrollToDemo() {
    document.getElementById('demo').scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
}

// ==========================================================================
// Add spin animation for loading spinners
// ==========================================================================

const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// ==========================================================================
// Initialize on page load
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 JARVIS Research OS Landing Page Loaded');
    console.log('✨ Interactive demos ready');
    
    // Add intersection observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
});
// ==========================================================================
// AOS (Animate On Scroll) Implementation
// ==========================================================================

class AOSAnimations {
    constructor() {
        this.elements = document.querySelectorAll('[data-aos]');
        this.options = {
            offset: 120,
            delay: 0,
            duration: 600,
            easing: 'ease',
            once: true
        };
        
        this.init();
    }
    
    init() {
        if (this.elements.length === 0) return;
        
        // Set initial styles
        this.elements.forEach(el => {
            const delay = el.dataset.aosDelay || this.options.delay;
            el.style.transitionDelay = `${delay}ms`;
            el.style.transitionDuration = `${this.options.duration}ms`;
            el.style.transitionTimingFunction = this.options.easing;
        });
        
        // Create observer
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('aos-animate');
                    if (this.options.once) {
                        observer.unobserve(entry.target);
                    }
                } else if (!this.options.once) {
                    entry.target.classList.remove('aos-animate');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: `-${this.options.offset}px 0px`
        });
        
        // Observe all elements
        this.elements.forEach(el => observer.observe(el));
    }
}

// ==========================================================================
// Counter Animation
// ==========================================================================

class CounterAnimation {
    constructor() {
        this.counters = document.querySelectorAll('[data-count]');
        this.init();
    }
    
    init() {
        if (this.counters.length === 0) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.5
        });
        
        this.counters.forEach(counter => observer.observe(counter));
    }
    
    animateCounter(element) {
        const target = parseFloat(element.dataset.count);
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                // Format number based on target
                if (target % 1 !== 0) {
                    // Decimal number
                    element.textContent = current.toFixed(1);
                } else {
                    // Integer
                    element.textContent = Math.floor(current).toLocaleString();
                }
                requestAnimationFrame(updateCounter);
            } else {
                // Final value
                if (target % 1 !== 0) {
                    element.textContent = target.toFixed(1);
                } else {
                    element.textContent = Math.floor(target).toLocaleString();
                }
            }
        };
        
        requestAnimationFrame(updateCounter);
    }
}

// ==========================================================================
// Parallax Effect
// ==========================================================================

class ParallaxEffect {
    constructor() {
        this.elements = document.querySelectorAll('[data-parallax="true"]');
        this.init();
    }
    
    init() {
        if (this.elements.length === 0) return;
        
        window.addEventListener('scroll', () => {
            requestAnimationFrame(() => this.update());
        });
    }
    
    update() {
        const scrollY = window.pageYOffset;
        
        this.elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const elementTop = rect.top + scrollY;
            const elementHeight = rect.height;
            const windowHeight = window.innerHeight;
            
            // Calculate parallax offset
            if (rect.top < windowHeight && rect.bottom > 0) {
                const offset = (scrollY - elementTop + windowHeight) / (windowHeight + elementHeight);
                const parallaxY = offset * 50 - 25; // -25 to 25 range
                
                el.style.transform = `translateY(${parallaxY}px)`;
            }
        });
    }
}

// ==========================================================================
// Code Tab Switching
// ==========================================================================

class CodeTabs {
    constructor() {
        this.tabs = document.querySelectorAll('.code-tab');
        this.panels = document.querySelectorAll('.code-panel');
        this.init();
    }
    
    init() {
        if (this.tabs.length === 0) return;
        
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab));
        });
    }
    
    switchTab(activeTab) {
        const targetId = activeTab.dataset.codeTab;
        
        // Remove active class from all tabs
        this.tabs.forEach(tab => tab.classList.remove('active'));
        this.panels.forEach(panel => panel.classList.remove('active'));
        
        // Add active class to selected tab and panel
        activeTab.classList.add('active');
        document.getElementById(`${targetId}-code`).classList.add('active');
    }
}

// ==========================================================================
// Code Copy Functionality
// ==========================================================================

function copyCode() {
    const activePanel = document.querySelector('.code-panel.active code');
    if (!activePanel) return;
    
    const text = activePanel.textContent;
    const button = document.querySelector('.code-copy-btn');
    
    navigator.clipboard.writeText(text).then(() => {
        // Success feedback
        button.classList.add('copied');
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M13.854 3.646a.5.5 0 010 .708l-7 7a.5.5 0 01-.708 0l-3.5-3.5a.5.5 0 11.708-.708L6.5 10.293l6.646-6.647a.5.5 0 01.708 0z"/>
            </svg>
            Copied!
        `;
        
        // Reset after 2 seconds
        setTimeout(() => {
            button.classList.remove('copied');
            button.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M4 2a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2H4zm0 2h8v8H4V4z"/>
                    <path d="M6 0a2 2 0 00-2 2h8a2 2 0 012 2v8a2 2 0 002-2V2a2 2 0 00-2-2H6z"/>
                </svg>
                Copy
            `;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// ==========================================================================
// Back to Top Button
// ==========================================================================

class BackToTop {
    constructor() {
        this.button = document.getElementById('backToTop');
        if (!this.button) return;
        
        this.init();
    }
    
    init() {
        // Show/hide on scroll
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                this.button.classList.add('visible');
            } else {
                this.button.classList.remove('visible');
            }
        });
        
        // Click handler
        this.button.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

// ==========================================================================
// Mobile Menu Toggle
// ==========================================================================

class MobileMenu {
    constructor() {
        this.button = document.getElementById('mobileMenuBtn');
        this.menu = document.querySelector('.nav-links');
        if (!this.button || !this.menu) return;
        
        this.init();
    }
    
    init() {
        this.button.addEventListener('click', () => {
            this.button.classList.toggle('active');
            this.menu.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
        
        // Close menu when clicking on a link
        const links = this.menu.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', () => {
                this.button.classList.remove('active');
                this.menu.classList.remove('active');
                document.body.classList.remove('menu-open');
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.button.contains(e.target) && !this.menu.contains(e.target)) {
                this.button.classList.remove('active');
                this.menu.classList.remove('active');
                document.body.classList.remove('menu-open');
            }
        });
    }
}

// ==========================================================================
// Smooth Scroll for Anchor Links
// ==========================================================================

class SmoothScroll {
    constructor() {
        this.links = document.querySelectorAll('a[href^="#"]');
        this.init();
    }
    
    init() {
        this.links.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (href === '#') return;
                
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    const offset = 80; // Navbar height
                    const targetPosition = target.offsetTop - offset;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
}

// ==========================================================================
// Lazy Load Images
// ==========================================================================

class LazyLoad {
    constructor() {
        this.images = document.querySelectorAll('img[data-src]');
        this.init();
    }
    
    init() {
        if (this.images.length === 0) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        this.images.forEach(img => observer.observe(img));
    }
}

// ==========================================================================
// Performance Monitoring
// ==========================================================================

class PerformanceMonitor {
    constructor() {
        this.init();
    }
    
    init() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = window.performance.timing;
                    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                    const connectTime = perfData.responseEnd - perfData.requestStart;
                    const renderTime = perfData.domComplete - perfData.domLoading;
                    
                    console.log('📊 Performance Metrics:');
                    console.log(`Page Load Time: ${pageLoadTime}ms`);
                    console.log(`Connect Time: ${connectTime}ms`);
                    console.log(`Render Time: ${renderTime}ms`);
                    
                    // Log to analytics if available
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'timing_complete', {
                            name: 'load',
                            value: pageLoadTime,
                            event_category: 'Performance'
                        });
                    }
                }, 0);
            });
        }
    }
}

// ==========================================================================
// Initialize Everything
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 JARVIS Research OS - Complete Landing Page Loaded');
    
    // Initialize all features
    new AOSAnimations();
    new CounterAnimation();
    new ParallaxEffect();
    new CodeTabs();
    new BackToTop();
    new MobileMenu();
    new SmoothScroll();
    new LazyLoad();
    new PerformanceMonitor();
    initializeApiConfigControls();
    
    // Add loaded class to body for CSS hooks
    document.body.classList.add('loaded');
    
    console.log('✨ All animations and interactions initialized');
});

// ==========================================================================
// Handle Window Resize
// ==========================================================================

let resizeTimer;
window.addEventListener('resize', () => {
    document.body.classList.add('resizing');
    
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        document.body.classList.remove('resizing');
        
        // Reinitialize parallax on resize
        const parallax = new ParallaxEffect();
    }, 250);
});

// ==========================================================================
// Keyboard Navigation
// ==========================================================================

document.addEventListener('keydown', (e) => {
    // Escape key to close mobile menu
    if (e.key === 'Escape') {
        const mobileMenu = document.querySelector('.nav-links.active');
        if (mobileMenu) {
            document.getElementById('mobileMenuBtn').click();
        }
    }
    
    // Ctrl/Cmd + K for search (placeholder)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        console.log('Search functionality placeholder');
    }
});

// ==========================================================================
// Visibility Change Handler
// ==========================================================================

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('⏸️ Page hidden');
    } else {
        console.log('▶️ Page visible');
    }
});

// ==========================================================================
// Export for external use
// ==========================================================================

window.JARVIS = {
    version: '1.0.0',
    scrollToDemo,
    runEvidenceGrading,
    runCitationAnalysis,
    runContradictionDetection,
    copyCode
};

console.log('🎯 JARVIS Research OS v1.0.0 Ready');
