export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        // CORS
        const corsHeaders = {
            "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        };
        if (request.method === "OPTIONS") return new Response("", { headers: corsHeaders });

        // === POST /api/run ===
        if (url.pathname === "/api/run" && request.method === "POST") {
            try {
                const body = await request.json();
                const { action, query, max_papers, turnstile_token } = body;

                // 1. Turnstile verify
                const verify = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: new URLSearchParams({
                        secret: env.TURNSTILE_SECRET_KEY,
                        response: turnstile_token,
                    }),
                }).then(r => r.json());

                if (!verify.success) {
                    return new Response(JSON.stringify({ ok: false, error: "turnstile_failed" }), {
                        status: 403, headers: { ...corsHeaders, "Content-Type": "application/json" },
                    });
                }

                // 2. Generate run_id
                const run_id = `${new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14)}-${crypto.randomUUID().slice(0, 6)}`;

                // 3. GitHub workflow_dispatch
                const owner = env.GITHUB_OWNER || "kaneko-ai";
                const repo = env.GITHUB_REPO || "jarvis-ml-pipeline";
                const workflow = env.GITHUB_WORKFLOW_FILE || "jarvis_dispatch.yml";

                const dispatchUrl = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;
                const resp = await fetch(dispatchUrl, {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
                        "Accept": "application/vnd.github+json",
                        "Content-Type": "application/json",
                        "User-Agent": "Cloudflare-Worker",
                    },
                    body: JSON.stringify({
                        ref: "main",
                        inputs: {
                            action: String(action || "report"),
                            query: String(query || ""),
                            max_papers: String(max_papers || "10"),
                            run_id,
                        }
                    }),
                });

                if (!resp.ok) {
                    const t = await resp.text();
                    return new Response(JSON.stringify({ ok: false, error: "dispatch_failed", detail: t }), {
                        status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" },
                    });
                }

                return new Response(JSON.stringify({ ok: true, run_id }), {
                    headers: { ...corsHeaders, "Content-Type": "application/json" },
                });

            } catch (e) {
                return new Response(JSON.stringify({ ok: false, error: e.message }), {
                    status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" },
                });
            }
        }

        // === GET /api/runs (proxy to gh-pages) ===
        if (url.pathname === "/api/runs" && request.method === "GET") {
            const owner = env.GITHUB_OWNER || "kaneko-ai";
            const repo = env.GITHUB_REPO || "jarvis-ml-pipeline";
            const ghPages = `https://${owner}.github.io/${repo}/runs/index.json`;

            const r = await fetch(ghPages, {
                headers: { "User-Agent": "Cloudflare-Worker" }
            });

            if (!r.ok) {
                return new Response(JSON.stringify({ ok: false, error: "failed_to_fetch_index", status: r.status }), {
                    status: r.status, headers: { ...corsHeaders, "Content-Type": "application/json" }
                });
            }

            return new Response(r.body, {
                headers: { ...corsHeaders, "Content-Type": "application/json" }
            });
        }

        return new Response(JSON.stringify({ ok: false, error: "not_found" }), {
            status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
    }
}
