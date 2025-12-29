type Target = {
  name: string;
  query: string;
  max_results: number;
  oa_only: boolean;
  domain?: string;
};

type Env = {
  JARVIS_API_BASE: string;
  JARVIS_API_TOKEN: string;
  DRY_RUN?: string;
  TIMEZONE?: string;
};

const TARGETS: Target[] = [
  {
    name: "cd73_batch",
    query: "CD73 OR NT5E",
    max_results: 100,
    oa_only: true,
    domain: "immunology",
  },
  {
    name: "cdh13_batch",
    query: "CDH13 OR T-cadherin",
    max_results: 100,
    oa_only: true,
    domain: "immunology",
  },
];

// 簡易的に「朝/夜」を判定（Cronが2回/日という前提で十分）
function computeSlot(nowUtc: Date): "slot_utc_0010" | "slot_utc_1210" | "slot_other" {
  const h = nowUtc.getUTCHours();
  const m = nowUtc.getUTCMinutes();
  if (h === 0 && m === 10) return "slot_utc_0010";
  if (h === 12 && m === 10) return "slot_utc_1210";
  return "slot_other";
}

function yyyymmddUtc(d: Date): string {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

async function postJob(env: Env, target: Target, dedupeKey: string): Promise<any> {
  const url = `${env.JARVIS_API_BASE.replace(/\/+$/, "")}/api/jobs`;
  const body = {
    type: "collect_and_ingest",
    payload: {
      query: target.query,
      max_results: target.max_results,
      oa_only: target.oa_only,
      domain: target.domain ?? null,
      // API側で重複抑止に使えるように入れておく（未対応でも無害）
      dedupe_key: dedupeKey,
      source: "cloudflare_cron",
      target_name: target.name,
    },
  };

  // DRY_RUN
  if ((env.DRY_RUN ?? "0") === "1") {
    return { dry_run: true, url, body };
  }

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.JARVIS_API_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { /* ignore */ }

  if (!res.ok) {
    throw new Error(`POST /api/jobs failed: status=${res.status}, body=${text}`);
  }

  return json ?? { ok: true, raw: text };
}

export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    const now = new Date();
    const slot = computeSlot(now);
    const date = yyyymmddUtc(now);

    const results: any[] = [];

    // ターゲットごとに投入。1件失敗しても他は続行。
    for (const t of TARGETS) {
      const dedupeKey = `${t.name}:${date}:${slot}`;
      try {
        const r = await postJob(env, t, dedupeKey);
        results.push({ target: t.name, dedupe_key: dedupeKey, result: r });
      } catch (e: any) {
        results.push({ target: t.name, dedupe_key: dedupeKey, error: String(e?.message ?? e) });
      }
    }

    // Cloudflareのログ（Workers dashboardで確認）
    console.log(JSON.stringify({
      kind: "jarvis_cron_enqueue",
      utc: now.toISOString(),
      slot,
      timezone: env.TIMEZONE ?? "unknown",
      api_base: env.JARVIS_API_BASE,
      dry_run: (env.DRY_RUN ?? "0") === "1",
      results,
    }));
  },
};
