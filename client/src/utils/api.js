const API_BASE = "http://localhost:5000/api/briefs";

export async function getBriefs(sessionId) {
  const res = await fetch(`${API_BASE}?client_session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error("Failed to fetch briefs");
  return await res.json();
}

export async function createBrief(sourceText, sessionId) {
  const res = await fetch(API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source_text: sourceText,
      client_session_id: sessionId,
    }),
  });
  if (!res.ok) throw new Error("Failed to create brief");
  return await res.json();
}

export async function getBrief(briefId, sessionId) {
  const res = await fetch(`${API_BASE}/${briefId}?client_session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error("Failed to fetch brief");
  return await res.json();
}

export async function deleteBrief(briefId, sessionId) {
  const res = await fetch(`${API_BASE}/${briefId}?client_session_id=${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 204) throw new Error("Failed to delete brief");
}