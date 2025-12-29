export type AlertPayload = Record<string, unknown>;

export async function notifyWebhook(
  webhookUrl: string,
  payload: AlertPayload,
): Promise<void> {
  await fetch(webhookUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
