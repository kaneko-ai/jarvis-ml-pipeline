import { notifyWebhook } from "./notify";

export type CronJobRequest = {
  type: string;
  payload: Record<string, unknown>;
  dedupe_key: string;
};

export type CronJobResult = {
  job_id?: string;
  status?: string;
  error?: string;
};

export async function submitCronJobs(
  apiBase: string,
  apiToken: string,
  jobs: CronJobRequest[],
  alertWebhookUrl?: string,
  alertLevel: string = "error",
): Promise<CronJobResult[]> {
  const results: CronJobResult[] = [];
  const failures: Array<{ target: string; error: string }> = [];

  for (const job of jobs) {
    if (!job.dedupe_key) {
      failures.push({ target: job.type, error: "dedupe_key missing" });
      results.push({ error: "dedupe_key missing" });
      continue;
    }

    try {
      const res = await fetch(`${apiBase}/api/jobs`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(job),
      });

      if (!res.ok) {
        const text = await res.text();
        failures.push({ target: job.type, error: text || res.statusText });
        results.push({ error: text || res.statusText });
        continue;
      }

      const data = (await res.json()) as CronJobResult;
      results.push(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      failures.push({ target: job.type, error: message });
      results.push({ error: message });
    }
  }

  if (alertWebhookUrl && failures.length > 0) {
    await notifyWebhook(alertWebhookUrl, {
      timestamp: new Date().toISOString(),
      level: alertLevel,
      api_base: apiBase,
      failures,
      successes: results.filter((result) => result.job_id),
    });
  }

  return results;
}
