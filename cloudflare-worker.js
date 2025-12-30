/**
 * Cloudflare Worker - GitHub Actions Dispatcher + Status API
 * 
 * Endpoints:
 * - POST /           : Trigger GitHub Actions (dispatch)
 * - GET /status      : Get run status (for UI polling)
 * - POST /status/update : Update run status (from GitHub Actions)
 * - POST /schedule/create : Create schedule (token required)
 * - POST /schedule/toggle : Toggle schedule enabled (token required)
 * - GET /schedule/list  : List schedules
 * 
 * Required Secrets:
 * - GITHUB_TOKEN     : GitHub PAT for workflow_dispatch
 * - TURNSTILE_SECRET_KEY : Turnstile verification
 * - STATUS_TOKEN     : Token for status/update authentication
 * - SCHEDULE_TOKEN   : Token for schedule write endpoints
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
            DEDUPE_TTL: parseInt(env.DEDUPE_TTL_SEC || '7200', 10),
            RUN_HISTORY_LIMIT: parseInt(env.SCHEDULE_RUN_HISTORY_LIMIT || '20', 10),
        };

        // === CORS Headers ===
        const corsHeaders = {
            'Access-Control-Allow-Origin': CONFIG.ALLOWED_ORIGIN,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Turnstile-Token, X-STATUS-TOKEN, X-SCHEDULE-TOKEN',
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

        // === POST /schedule/create ===
        if (url.pathname === '/schedule/create' && request.method === 'POST') {
            const authError = requireScheduleToken(request, env);
            if (authError) {
                return json({ ok: false, error: authError }, 401, corsHeaders);
            }

            if (!env.STATUS_KV) {
                return json({ ok: false, error: 'KV not configured' }, 500, corsHeaders);
            }

            const body = await request.json();
            const query = (body.query || '').trim();
            const freq = parseInt(body.freq, 10);
            const enabled = body.enabled !== false;

            if (!query) {
                return json({ ok: false, error: 'query required' }, 400, corsHeaders);
            }

            if (!Number.isFinite(freq) || freq < 1) {
                return json({ ok: false, error: 'freq must be >= 1 (minutes)' }, 400, corsHeaders);
            }

            const schedule = {
                id: `schedule_${generateRunId()}`,
                query,
                freq,
                enabled,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                last_run_at: null,
                last_run_id: null,
                runs: [],
            };

            await env.STATUS_KV.put(`schedules:${schedule.id}`, JSON.stringify(schedule));
            await addScheduleIndex(env.STATUS_KV, schedule.id);

            return json({ ok: true, schedule }, 200, corsHeaders);
        }

        // === POST /schedule/toggle ===
        if (url.pathname === '/schedule/toggle' && request.method === 'POST') {
            const authError = requireScheduleToken(request, env);
            if (authError) {
                return json({ ok: false, error: authError }, 401, corsHeaders);
            }

            if (!env.STATUS_KV) {
                return json({ ok: false, error: 'KV not configured' }, 500, corsHeaders);
            }

            const body = await request.json();
            const id = body.id;
            const enabled = body.enabled === true;

            if (!id) {
                return json({ ok: false, error: 'id required' }, 400, corsHeaders);
            }

            const raw = await env.STATUS_KV.get(`schedules:${id}`);
            if (!raw) {
                return json({ ok: false, error: 'schedule not found' }, 404, corsHeaders);
            }

            const schedule = JSON.parse(raw);
            schedule.enabled = enabled;
            schedule.updated_at = new Date().toISOString();
            await env.STATUS_KV.put(`schedules:${id}`, JSON.stringify(schedule));

            return json({ ok: true, schedule }, 200, corsHeaders);
        }

        // === GET /schedule/list ===
        if (url.pathname === '/schedule/list' && request.method === 'GET') {
            if (!env.STATUS_KV) {
                return json({ ok: true, schedules: [], note: 'KV not configured' }, 200, corsHeaders);
            }

            const ids = await getScheduleIndex(env.STATUS_KV);
            const schedules = [];
            for (const id of ids) {
                const raw = await env.STATUS_KV.get(`schedules:${id}`);
                if (raw) {
                    schedules.push(JSON.parse(raw));
                }
            }
            schedules.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''));
            return json({ ok: true, schedules }, 200, corsHeaders);
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
    async scheduled(event, env, ctx) {
        const CONFIG = {
            GITHUB_OWNER: env.GITHUB_OWNER || 'kaneko-ai',
            GITHUB_REPO: env.GITHUB_REPO || 'jarvis-ml-pipeline',
            GITHUB_WORKFLOW_FILE: env.GITHUB_WORKFLOW_FILE || 'jarvis_dispatch.yml',
            STATUS_TTL: parseInt(env.STATUS_TTL_SEC || '86400', 10),
            DEDUPE_TTL: parseInt(env.DEDUPE_TTL_SEC || '7200', 10),
            RUN_HISTORY_LIMIT: parseInt(env.SCHEDULE_RUN_HISTORY_LIMIT || '20', 10),
        };

        if (!env.STATUS_KV) {
            return;
        }

        const ids = await getScheduleIndex(env.STATUS_KV);
        const now = new Date();
        const hourKey = formatHourKey(now);

        for (const id of ids) {
            const raw = await env.STATUS_KV.get(`schedules:${id}`);
            if (!raw) {
                continue;
            }

            const schedule = JSON.parse(raw);
            if (!schedule.enabled) {
                continue;
            }

            if (!shouldRunSchedule(schedule, now)) {
                continue;
            }

            const dedupeKey = `dedupe:${schedule.id}:${hourKey}`;
            const already = await env.STATUS_KV.get(dedupeKey);
            if (already) {
                continue;
            }

            const runId = generateRunId();
            const initialStatus = {
                run_id: runId,
                percent: 0,
                stage: 'queued',
                message: 'Waiting for GitHub Actions to start',
                counters: { query: schedule.query || '' },
                updated_at: new Date().toISOString(),
            };
            await env.STATUS_KV.put(`run:${runId}`, JSON.stringify(initialStatus), { expirationTtl: CONFIG.STATUS_TTL });

            const dispatchResult = await triggerGitHubAction(
                {
                    action: 'pipeline',
                    query: schedule.query || '',
                    max_results: String(schedule.max_results || 10),
                    date_from: schedule.date_from || '',
                    date_to: schedule.date_to || '',
                    run_id: runId,
                },
                env.GITHUB_TOKEN,
                CONFIG
            );

            if (!dispatchResult.success) {
                continue;
            }

            await env.STATUS_KV.put(dedupeKey, runId, { expirationTtl: CONFIG.DEDUPE_TTL });

            const runEntry = { run_id: runId, at: now.toISOString() };
            schedule.last_run_at = runEntry.at;
            schedule.last_run_id = runId;
            schedule.updated_at = runEntry.at;
            schedule.runs = [runEntry, ...(schedule.runs || [])].slice(0, CONFIG.RUN_HISTORY_LIMIT);

            await env.STATUS_KV.put(`schedules:${schedule.id}`, JSON.stringify(schedule));
        }
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

function requireScheduleToken(request, env) {
    const token = request.headers.get('X-SCHEDULE-TOKEN');
    if (!token || token !== env.SCHEDULE_TOKEN) {
        return 'unauthorized';
    }
    return null;
}

async function getScheduleIndex(kv) {
    const raw = await kv.get('schedules:index');
    if (!raw) return [];
    try {
        const ids = JSON.parse(raw);
        return Array.isArray(ids) ? ids : [];
    } catch (error) {
        return [];
    }
}

async function addScheduleIndex(kv, id) {
    const ids = await getScheduleIndex(kv);
    if (!ids.includes(id)) {
        ids.push(id);
        await kv.put('schedules:index', JSON.stringify(ids));
    }
}

function shouldRunSchedule(schedule, now) {
    const freq = parseInt(schedule.freq, 10);
    if (!Number.isFinite(freq) || freq < 1) {
        return false;
    }

    if (!schedule.last_run_at) {
        return true;
    }

    const last = new Date(schedule.last_run_at);
    const diffMinutes = (now - last) / 60000;
    return diffMinutes >= freq;
}

function formatHourKey(now) {
    const pad = (value) => String(value).padStart(2, '0');
    return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}`;
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
