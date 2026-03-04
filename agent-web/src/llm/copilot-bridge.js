const COPILOT_API_URL = process.env.COPILOT_API_URL || "http://localhost:4141";
const FETCH_TIMEOUT_MS = 60000; // 60 seconds

const SYSTEM_PROMPT = [
  "あなたはJARVIS Research OSの研究アシスタントです。",
  "生物医学研究（PD-1免疫療法、スペルミジン、オートファジー、免疫老化など）の",
  "メタ分析と文献レビューを専門としています。",
  "回答は日本語で、学術的に正確に行ってください。",
].join("");

function fetchWithTimeout(url, options, timeoutMs = FETCH_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { ...options, signal: controller.signal }).finally(() =>
    clearTimeout(timer)
  );
}

export async function callCopilotLLM({
  message,
  model = "gpt-4.1",
  history = [],
  systemPrompt = "",
}) {
  const messages = [];
  messages.push({ role: "system", content: systemPrompt || SYSTEM_PROMPT });

  for (const msg of history) {
    messages.push({ role: msg.role, content: msg.content });
  }
  messages.push({ role: "user", content: message });

  const response = await fetchWithTimeout(
    `${COPILOT_API_URL}/v1/chat/completions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer dummy",
      },
      body: JSON.stringify({
        model,
        messages,
        stream: false,
        temperature: 0.3,
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Copilot API error (${response.status}): ${errorText}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || "";

  return {
    success: true,
    content,
    model,
    usage: data.usage || {},
  };
}

export async function callCopilotLLMStream({
  message,
  model = "gpt-4.1",
  history = [],
  systemPrompt = "",
}) {
  const messages = [];
  messages.push({ role: "system", content: systemPrompt || SYSTEM_PROMPT });

  for (const msg of history) {
    messages.push({ role: msg.role, content: msg.content });
  }
  messages.push({ role: "user", content: message });

  const response = await fetchWithTimeout(
    `${COPILOT_API_URL}/v1/chat/completions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer dummy",
      },
      body: JSON.stringify({
        model,
        messages,
        stream: true,
        temperature: 0.3,
      }),
    },
    120000 // streaming is longer: 120s
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Copilot API error (${response.status}): ${errorText}`);
  }

  return response.body;
}

export async function listCopilotModels() {
  try {
    const response = await fetchWithTimeout(
      `${COPILOT_API_URL}/v1/models`,
      { headers: { Authorization: "Bearer dummy" } },
      10000 // 10s for model list
    );
    if (!response.ok) return [];
    const data = await response.json();
    return data.data || [];
  } catch {
    return [];
  }
}
