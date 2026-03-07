const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request mislukt: ${response.status}`);
  }

  return response.json();
}

export function getOverview() {
  return request("/api/overview");
}

export function getVoiceBlueprint() {
  return request("/api/voice/blueprint");
}

export function getSetupStatus() {
  return request("/api/setup/status");
}

export function getActivity() {
  return request("/api/activity");
}

export function sendChat(message, sessionId = "dashboard", confirmationToken = null) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      message,
      confirmation_token: confirmationToken
    })
  });
}

export function executeTool(toolName, payload, confirmationToken = null) {
  return request(`/api/tools/${toolName}`, {
    method: "POST",
    body: JSON.stringify({
      payload,
      confirmation_token: confirmationToken
    })
  });
}

export async function transcribeVoice(audioBlob) {
  const response = await fetch(`${API_BASE}/api/voice/transcribe`, {
    method: "POST",
    headers: {
      "Content-Type": "audio/wav"
    },
    body: audioBlob
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Transcriptie mislukt: ${response.status}`);
  }

  return response.json();
}

export async function speakText(text) {
  const response = await fetch(`${API_BASE}/api/voice/speak`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Spraaksynthese mislukt: ${response.status}`);
  }

  return response.blob();
}
