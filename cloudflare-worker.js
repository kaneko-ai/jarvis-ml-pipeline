/**
 * Cloudflare Worker - GitHub Actions Dispatcher + Status API
 * 
 * Endpoints:
 * - POST /           : Trigger GitHub Actions (dispatch)
 * - GET /status      : Get run status (for UI polling)
 * - POST /status/update : Update run status (from GitHub Actions)
 * 
 * Required Secrets:
 * - GITHUB_TOKEN     : GitHub PAT for workflow_dispatch
 * - TURNSTILE_SECRET_KEY : Turnstile verification
 * - STATUS_TOKEN     : Token for status/update authentication
 * 
 * Required KV Binding:
 * - STATUS_KV        : KV namespace for status storage
 */

export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        // === Configuration ===
        const CONFIG = {
            ALLOWED_ORIGIN: '*',
            GITHUB_OWNER: env.GITHUB_OWNER || 'kaneko-ai',
            GITHUB_REPO: env.GITHUB_REPO || 'jarvis-ml-pipeline',
            GITHUB_WORKFLOW_FILE: env.GITHUB_WORKFLOW_FILE || 'jarvis_dispatch.yml',
            STATUS_TTL: parseInt(env.STATUS_TTL_SEC || '86400', 10), // 24h default
        };

        // === CORS Headers ===
        const corsHeaders = {
            'Access-Control-Allow-Origin': CONFIG.ALLOWED_ORIGIN,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Turnstile-Token, X-STATUS-TOKEN',
        };

        // Handle CORS preflight
        if (request.method === 'OPTIONS') {
            return new Response(null, { status: 204, headers: corsHeaders });
        }

        // === GET /status?run_id=... ===
        if (url.pathname === '/status' && request.method === 'GET') {
            const runId = url.searchParams.get('run_id');
            if (!runId) {
                return json({ ok: false, error: 'run_id required' }, 400, corsHeaders);
            }

            // Check if KV is available
            if (!env.STATUS_KV) {
                return json({ ok: true, run_id: runId, status: null, note: 'KV not configured' }, 200, corsHeaders);
            }

            const raw = await env.STATUS_KV.get(`run:${runId}`);
            if (!raw) {
                return json({ ok: true, run_id: runId, status: null }, 200, corsHeaders);
            }

            return json({ ok: true, run_id: runId, status: JSON.parse(raw) }, 200, corsHeaders);
        }

        // === POST /status/update ===
        if (url.pathname === '/status/update' && request.method === 'POST') {
            const token = request.headers.get('X-STATUS-TOKEN');
            if (!token || token !== env.STATUS_TOKEN) {
                return json({ ok: false, error: 'unauthorized' }, 401, corsHeaders);
            }

            const body = await request.json();
            const runId = body.run_id;
            if (!runId) {
                return json({ ok: false, error: 'run_id required' }, 400, corsHeaders);
            }

            // Optional: UUID format validation
            if (!/^[0-9a-zA-Z_-]{8,64}$/.test(runId)) {
                return json({ ok: false, error: 'invalid run_id format' }, 400, corsHeaders);
            }

            const status = {
                run_id: runId,
                percent: body.percent ?? 0,
                stage: body.stage ?? 'unknown',
                message: body.message ?? '',
                counters: body.counters ?? {},
                updated_at: new Date().toISOString(),
            };

            // Store in KV if available
            if (env.STATUS_KV) {
                await env.STATUS_KV.put(`run:${runId}`, JSON.stringify(status), { expirationTtl: CONFIG.STATUS_TTL });
            }

            return json({ ok: true }, 200, corsHeaders);
        }

        // === POST / (dispatch - existing functionality) ===
        if (request.method === 'POST' && (url.pathname === '/' || url.pathname === '/dispatch')) {
            try {
                const body = await request.json();
                const { turnstile_token, action, query, max_results, date_from, date_to, client_run_id } = body;

                // 1. Verify Turnstile
                const turnstileValid = await verifyTurnstile(turnstile_token, env.TURNSTILE_SECRET_KEY);
                if (!turnstileValid) {
                    return json({ error: 'Turnstile validation failed' }, 403, corsHeaders);
                }

                // 2. Generate or use client_run_id
                const run_id = client_run_id || generateRunId();

                // 3. Initialize status in KV (if available)
                if (env.STATUS_KV) {
                    const initialStatus = {
                        run_id: run_id,
                        percent: 0,
                        stage: 'queued',
                        message: 'Waiting for GitHub Actions to start',
                        counters: { query: query || '' },
                        updated_at: new Date().toISOString(),
                    };
                    await env.STATUS_KV.put(`run:${run_id}`, JSON.stringify(initialStatus), { expirationTtl: CONFIG.STATUS_TTL });
                }

                // 4. Trigger GitHub Actions
                const dispatchResult = await triggerGitHubAction(
                    {
                        action: action || 'pipeline',
                        query: query || '',
                        max_results: String(max_results || 10),
                        date_from: date_from || '',
                        date_to: date_to || '',
                        run_id: run_id, // Pass run_id to workflow
                    },
                    env.GITHUB_TOKEN,
                    CONFIG
                );

                if (!dispatchResult.success) {
                    return json({ error: dispatchResult.error }, 500, corsHeaders);
                }

                // 5. Return run_id for UI to track
                return json({
                    ok: true,
                    status: 'queued',
                    message: 'GitHub Actions triggered successfully',
                    run_id: run_id,
                }, 200, corsHeaders);

            } catch (error) {
                return json({ error: error.message }, 500, corsHeaders);
            }
        }

        // === Fallback: Not Found ===
        return json({ ok: false, error: 'not found' }, 404, corsHeaders);
    },
};

// === Helper Functions ===

function json(obj, status = 200, headers = {}) {
    return new Response(JSON.stringify(obj), {
        status,
        headers: { 'Content-Type': 'application/json', ...headers },
    });
}

async function verifyTurnstile(token, secretKey) {
    if (!token || !secretKey) return false;
    const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret: secretKey, response: token }),
    });
    const data = await res.json();
    return data.success === true;
}

function generateRunId() {
    const now = new Date();
    const timestamp = now.toISOString().slice(0, 19).replace(/[-:T]/g, '').slice(0, 14);
    const rand = Math.random().toString(36).substring(2, 10);
    return `${timestamp}_${rand}`;
}

async function triggerGitHubAction(inputs, token, config) {
    if (!token) return { success: false, error: 'Missing GITHUB_TOKEN secret' };

    const url = `https://api.github.com/repos/${config.GITHUB_OWNER}/${config.GITHUB_REPO}/actions/workflows/${config.GITHUB_WORKFLOW_FILE}/dispatches`;

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'User-Agent': 'Cloudflare-Worker'
        },
        body: JSON.stringify({ ref: 'main', inputs }),
    });

    if (res.ok) return { success: true };
    const error = await res.text();
    return { success: false, error: `GitHub API error: ${res.status} - ${error}` };
}
