/**
 * Cloudflare Worker - GitHub Actions Dispatcher
 * 
 * このWorkerは以下を行います:
 * 1. CORS検証（ALLOWED_ORIGINチェック）
 * 2. Turnstile token検証（siteverify）
 * 3. run_id生成（YYYYMMDD_HHMMSS_rand）
 * 4. GitHub API workflow_dispatch実行
 * 5. {run_id, status:"queued"} 返却
 * 
 * 必要なSecrets（Cloudflare Dashboard → Workers → Settings → Variables）:
 * - GITHUB_TOKEN: workflow実行権限を持つPAT
 * - GITHUB_OWNER: kaneko-ai
 * - GITHUB_REPO: jarvis-ml-pipeline
 * - GITHUB_WORKFLOW_FILE: jarvis_dispatch.yml
 * - TURNSTILE_SECRET_KEY: Turnstile検証用
 * - ALLOWED_ORIGIN: https://kaneko-ai.github.io
 */

export default {
    async fetch(request, env) {
        // CORS preflight
        if (request.method === 'OPTIONS') {
            return handleCORS(env);
        }

        // POSTのみ許可
        if (request.method !== 'POST') {
            return new Response('Method Not Allowed', { status: 405 });
        }

        // CORS検証
        const origin = request.headers.get('Origin');
        if (!origin || origin !== env.ALLOWED_ORIGIN) {
            return new Response('Forbidden - Invalid Origin', { status: 403 });
        }

        try {
            // リクエストボディ解析
            const body = await request.json();
            const { turnstile_token, action, query, max_results, date_from, date_to } = body;

            // Turnstile検証
            const turnstileValid = await verifyTurnstile(turnstile_token, env);
            if (!turnstileValid) {
                return new Response(JSON.stringify({ error: 'Turnstile validation failed' }), {
                    status: 403,
                    headers: { 'Content-Type': 'application/json' },
                });
            }

            // run_id生成
            const run_id = generateRunId();

            // GitHub Actionsをトリガー
            const dispatchResult = await triggerGitHubAction(
                {
                    action: action || 'pipeline',
                    query: query || '',
                    max_results: max_results || 10,
                    date_from: date_from || '',
                    date_to: date_to || '',
                    run_id,
                },
                env
            );

            if (!dispatchResult.success) {
                return new Response(JSON.stringify({ error: dispatchResult.error }), {
                    status: 500,
                    headers: getCORSHeaders(env),
                });
            }

            // 成功レスポンス
            return new Response(
                JSON.stringify({
                    run_id,
                    status: 'queued',
                    message: 'GitHub Actions triggered successfully',
                }),
                {
                    status: 200,
                    headers: getCORSHeaders(env),
                }
            );
        } catch (error) {
            return new Response(JSON.stringify({ error: error.message }), {
                status: 500,
                headers: getCORSHeaders(env),
            });
        }
    },
};

/**
 * Turnstile検証
 */
async function verifyTurnstile(token, env) {
    if (!token) return false;

    const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            secret: env.TURNSTILE_SECRET_KEY,
            response: token,
        }),
    });

    const data = await res.json();
    return data.success === true;
}

/**
 * run_id生成
 */
function generateRunId() {
    const now = new Date();
    const timestamp = now.toISOString().slice(0, 19).replace(/[-:T]/g, '').slice(0, 14); // YYYYMMDDHHMMSS
    const rand = Math.random().toString(36).substring(2, 10);
    return `${timestamp}_${rand}`;
}

/**
 * GitHub Actions workflow_dispatch実行
 */
async function triggerGitHubAction(inputs, env) {
    const url = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW_FILE}/dispatches`;

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'User-Agent': 'Cloudflare-Worker',
        },
        body: JSON.stringify({
            ref: 'main', // または master
            inputs,
        }),
    });

    if (res.ok) {
        return { success: true };
    } else {
        const error = await res.text();
        return { success: false, error: `GitHub API error: ${res.status} - ${error}` };
    }
}

/**
 * CORS headers
 */
function getCORSHeaders(env) {
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    };
}

/**
 * CORS preflight response
 */
function handleCORS(env) {
    return new Response(null, {
        status: 204,
        headers: getCORSHeaders(env),
    });
}
