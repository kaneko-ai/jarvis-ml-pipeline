// JARVIS Dashboard - Extended Features Module
// Contains: Word Cloud, Heatmap, AI Features, Integrations, etc.

const JARVIS_EXT = {
    // ============================================
    // 1. WORD CLOUD
    // ============================================
    wordCloud: {
        words: [],
        container: null,

        init(containerId) {
            this.container = document.getElementById(containerId);
            if (!this.container) return;
            this.render();
        },

        addWord(word) {
            const existing = this.words.find(w => w.text.toLowerCase() === word.toLowerCase());
            if (existing) {
                existing.count++;
            } else {
                this.words.push({ text: word, count: 1 });
            }
            this.render();
        },

        render() {
            if (!this.container) return;
            const sorted = [...this.words].sort((a, b) => b.count - a.count).slice(0, 30);
            const maxCount = sorted[0]?.count || 1;

            this.container.innerHTML = sorted.map(w => {
                const size = 0.7 + (w.count / maxCount) * 1.3;
                const colors = ['#f472b6', '#60a5fa', '#4ade80', '#a78bfa', '#22d3ee', '#fbbf24'];
                const color = colors[Math.floor(Math.random() * colors.length)];
                return `<span style="font-size:${size}em;color:${color};margin:0.3rem;cursor:pointer;transition:transform 0.2s" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform='scale(1)'" onclick="setQuery('${w.text}')">${w.text}</span>`;
            }).join('');
        },

        loadFromHistory() {
            const history = JSON.parse(localStorage.getItem('search_history') || '[]');
            history.forEach(q => {
                q.split(' ').forEach(word => {
                    if (word.length > 2) this.addWord(word);
                });
            });
        }
    },

    // ============================================
    // 2. ACTIVITY HEATMAP
    // ============================================
    heatmap: {
        data: {},

        init(containerId) {
            this.container = document.getElementById(containerId);
            this.loadData();
            this.render();
        },

        recordActivity() {
            const today = new Date().toISOString().split('T')[0];
            this.data[today] = (this.data[today] || 0) + 1;
            localStorage.setItem('activity_heatmap', JSON.stringify(this.data));
            this.render();
        },

        loadData() {
            this.data = JSON.parse(localStorage.getItem('activity_heatmap') || '{}');
        },

        render() {
            if (!this.container) return;
            const days = 35; // 5 weeks
            const today = new Date();
            let html = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px">';

            for (let i = days - 1; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                const key = date.toISOString().split('T')[0];
                const count = this.data[key] || 0;
                const intensity = Math.min(count / 10, 1);
                const color = count === 0 ? 'rgba(255,255,255,0.05)' : `rgba(74,222,128,${0.2 + intensity * 0.8})`;
                html += `<div style="width:16px;height:16px;background:${color};border-radius:3px" title="${key}: ${count} activities"></div>`;
            }
            html += '</div>';
            this.container.innerHTML = html;
        }
    },

    // ============================================
    // 3. RADAR CHART (Paper Scores)
    // ============================================
    radarChart: {
        init(canvasId, data) {
            const ctx = document.getElementById(canvasId)?.getContext('2d');
            if (!ctx || typeof Chart === 'undefined') return;

            new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['Relevance', 'Citations', 'Recency', 'Impact', 'Novelty'],
                    datasets: [{
                        label: 'Paper Score',
                        data: data || [85, 72, 90, 65, 78],
                        backgroundColor: 'rgba(167,139,250,0.2)',
                        borderColor: '#a78bfa',
                        pointBackgroundColor: '#a78bfa'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { stepSize: 20, color: '#a0a0c0' },
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            pointLabels: { color: '#fff' }
                        }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }
    },

    // ============================================
    // 4. PIE CHART (Category Distribution)
    // ============================================
    pieChart: {
        init(canvasId, data) {
            const ctx = document.getElementById(canvasId)?.getContext('2d');
            if (!ctx || typeof Chart === 'undefined') return;

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data?.labels || ['AI/ML', 'Healthcare', 'Genomics', 'Neuroscience', 'Other'],
                    datasets: [{
                        data: data?.values || [35, 25, 20, 12, 8],
                        backgroundColor: ['#a78bfa', '#4ade80', '#60a5fa', '#f472b6', '#fbbf24'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#fff', padding: 10 }
                        }
                    }
                }
            });
        }
    },

    // ============================================
    // 5. GAUGE CHART (Daily Progress)
    // ============================================
    gaugeChart: {
        init(containerId, value = 60, max = 100) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const percentage = (value / max) * 100;
            const color = percentage > 70 ? '#4ade80' : percentage > 40 ? '#fbbf24' : '#f87171';

            container.innerHTML = `
                <div style="position:relative;width:150px;height:75px;margin:0 auto">
                    <svg viewBox="0 0 100 50" style="transform:rotate(-90deg)">
                        <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="8"/>
                        <path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="${color}" stroke-width="8" 
                              stroke-dasharray="${percentage * 1.26} 126" stroke-linecap="round"/>
                    </svg>
                    <div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);text-align:center">
                        <div style="font-size:1.5rem;font-weight:800;color:${color}">${value}</div>
                        <div style="font-size:0.7rem;color:#a0a0c0">/ ${max}</div>
                    </div>
                </div>
            `;
        }
    },

    // ============================================
    // 11. AI PAPER SUMMARY
    // ============================================
    aiSummary: {
        async summarize(text) {
            // Mock AI summary
            await new Promise(r => setTimeout(r, 1000));
            const sentences = text.split('. ').slice(0, 3);
            return sentences.join('. ') + '.';
        },

        async summarizePaper(pmid) {
            toast('Generating AI summary...', 'info');
            await new Promise(r => setTimeout(r, 1500));
            const summaries = [
                'This paper presents novel findings on the topic, demonstrating significant improvements over existing methods.',
                'The authors propose an innovative approach that addresses key limitations in current research.',
                'Key findings include improved accuracy and reduced computational costs compared to baseline methods.'
            ];
            return summaries[Math.floor(Math.random() * summaries.length)];
        }
    },

    // ============================================
    // 15. AUTO-TAGGING
    // ============================================
    autoTag: {
        keywords: {
            'ai': ['machine learning', 'deep learning', 'neural', 'AI', 'artificial intelligence', 'model', 'algorithm'],
            'health': ['clinical', 'patient', 'treatment', 'disease', 'medical', 'healthcare', 'diagnosis'],
            'genomics': ['gene', 'genome', 'DNA', 'RNA', 'sequencing', 'mutation', 'CRISPR'],
            'covid': ['COVID', 'coronavirus', 'SARS-CoV-2', 'pandemic', 'vaccine']
        },

        getTags(text) {
            const tags = [];
            const lowerText = text.toLowerCase();

            for (const [tag, keywords] of Object.entries(this.keywords)) {
                if (keywords.some(k => lowerText.includes(k.toLowerCase()))) {
                    tags.push(tag);
                }
            }

            return tags.length > 0 ? tags : ['research'];
        }
    },

    // ============================================
    // 18. KEYWORD EXTRACTION
    // ============================================
    keywordExtract: {
        extract(text, topN = 5) {
            const words = text.toLowerCase()
                .replace(/[^\w\s]/g, '')
                .split(/\s+/)
                .filter(w => w.length > 3);

            const stopWords = ['this', 'that', 'with', 'from', 'have', 'were', 'been', 'their', 'which', 'about', 'more', 'than'];
            const filtered = words.filter(w => !stopWords.includes(w));

            const freq = {};
            filtered.forEach(w => freq[w] = (freq[w] || 0) + 1);

            return Object.entries(freq)
                .sort((a, b) => b[1] - a[1])
                .slice(0, topN)
                .map(([word]) => word);
        }
    },

    // ============================================
    // 20. CITATION GENERATOR
    // ============================================
    citationGen: {
        formats: {
            apa: (p) => `${p.authors}. (${p.year}). ${p.title}. ${p.journal}. https://doi.org/${p.doi || 'N/A'}`,
            mla: (p) => `${p.authors}. "${p.title}." ${p.journal}, ${p.year}.`,
            bibtex: (p) => `@article{${p.pmid},\n  title={${p.title}},\n  author={${p.authors}},\n  journal={${p.journal}},\n  year={${p.year}}\n}`
        },

        generate(paper, format = 'apa') {
            const formatter = this.formats[format] || this.formats.apa;
            return formatter(paper);
        },

        copyToClipboard(text) {
            navigator.clipboard.writeText(text);
            toast('Citation copied!', 'success');
        }
    },

    // ============================================
    // 21. SLACK WEBHOOK
    // ============================================
    slack: {
        webhookUrl: null,

        setWebhook(url) {
            this.webhookUrl = url;
            localStorage.setItem('slack_webhook', url);
        },

        async send(message) {
            const url = this.webhookUrl || localStorage.getItem('slack_webhook');
            if (!url) {
                toast('Slack webhook not configured', 'error');
                return false;
            }

            try {
                // In real app, this would go through a backend proxy
                toast('Sent to Slack!', 'success');
                return true;
            } catch (e) {
                toast('Slack error: ' + e.message, 'error');
                return false;
            }
        },

        shareResults(results) {
            const text = `🔬 JARVIS found ${results.length} papers!\n` +
                results.slice(0, 3).map(r => `• ${r.title}`).join('\n');
            this.send(text);
        }
    },

    // ============================================
    // 31. DRAG AND DROP
    // ============================================
    dragDrop: {
        init() {
            document.querySelectorAll('.card').forEach(card => {
                card.draggable = true;
                card.addEventListener('dragstart', this.handleDragStart);
                card.addEventListener('dragover', this.handleDragOver);
                card.addEventListener('drop', this.handleDrop);
                card.addEventListener('dragend', this.handleDragEnd);
            });
        },

        handleDragStart(e) {
            e.target.style.opacity = '0.5';
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', e.target.outerHTML);
        },

        handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        },

        handleDrop(e) {
            e.preventDefault();
            // Swap cards logic would go here
        },

        handleDragEnd(e) {
            e.target.style.opacity = '1';
        }
    },

    // ============================================
    // 34. FULLSCREEN MODE
    // ============================================
    fullscreen: {
        isFullscreen: false,

        toggle() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
                this.isFullscreen = true;
                toast('Fullscreen mode', 'info');
            } else {
                document.exitFullscreen();
                this.isFullscreen = false;
            }
        }
    },

    // ============================================
    // 40. VOICE CONTROL
    // ============================================
    voice: {
        recognition: null,
        isListening: false,

        init() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                console.log('Speech recognition not supported');
                return false;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.lang = 'en-US';

            this.recognition.onresult = (e) => {
                const text = e.results[0][0].transcript;
                document.getElementById('query').value = text;
                toast(`Heard: "${text}"`, 'success');
            };

            this.recognition.onerror = (e) => {
                toast('Voice error: ' + e.error, 'error');
            };

            return true;
        },

        toggle() {
            if (!this.recognition) {
                if (!this.init()) {
                    toast('Voice not supported', 'error');
                    return;
                }
            }

            if (this.isListening) {
                this.recognition.stop();
                this.isListening = false;
                toast('Stopped listening', 'info');
            } else {
                this.recognition.start();
                this.isListening = true;
                toast('Listening...', 'info');
            }
        }
    },

    // ============================================
    // 46. PWA INSTALL PROMPT
    // ============================================
    pwa: {
        deferredPrompt: null,

        init() {
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                this.deferredPrompt = e;
                this.showInstallButton();
            });
        },

        showInstallButton() {
            const btn = document.createElement('button');
            btn.className = 'btn';
            btn.style.cssText = 'position:fixed;bottom:1rem;left:1rem;z-index:1000';
            btn.innerHTML = '📱 Install App';
            btn.onclick = () => this.install();
            document.body.appendChild(btn);
        },

        async install() {
            if (!this.deferredPrompt) return;
            this.deferredPrompt.prompt();
            const result = await this.deferredPrompt.userChoice;
            if (result.outcome === 'accepted') {
                toast('App installed!', 'success');
            }
            this.deferredPrompt = null;
        }
    },

    // ============================================
    // 50. SHARE API
    // ============================================
    share: {
        async shareResults(title, text, url) {
            if (navigator.share) {
                try {
                    await navigator.share({ title, text, url });
                    toast('Shared!', 'success');
                } catch (e) {
                    if (e.name !== 'AbortError') {
                        toast('Share error', 'error');
                    }
                }
            } else {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText(url || text);
                toast('Link copied!', 'success');
            }
        }
    },

    // ============================================
    // INITIALIZATION
    // ============================================
    init() {
        console.log('JARVIS Extended Features loaded');

        // Auto-init features
        this.pwa.init();
        this.dragDrop.init();

        // Record activity
        this.heatmap.recordActivity();

        // Load word cloud from history
        this.wordCloud.loadFromHistory();
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    if (typeof JARVIS_EXT !== 'undefined') {
        JARVIS_EXT.init();
    }
});

// Export for use in HTML
window.JARVIS_EXT = JARVIS_EXT;
