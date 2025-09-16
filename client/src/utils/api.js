const API_BASE = process.env.REACT_APP_API_URL ? 
  `${process.env.REACT_APP_API_URL}/api/briefs` : 
  "https://briefme.onrender.com/api/briefs";

const API_TIMEOUT = 60000; // 15+45 seconds

export async function getBriefs(sessionId) {
  if (!sessionId) throw new Error("Session ID is required");
  
  console.log("Fetching briefs with session ID:", sessionId);
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
  
  const url = `${API_BASE}?client_session_id=${encodeURIComponent(sessionId)}`;
  console.log("Fetching from URL:", url);
  
  try {
    const res = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error("GET briefs error:", res.status, errorText);
      if (res.status >= 500) {
        throw new Error("Server error - please try again later");
      }
      throw new Error("Failed to fetch briefs");
    }
    
    const data = await res.json();
    return Array.isArray(data) ? data : []; // Ensure array return
  } catch (error) {
    clearTimeout(timeoutId);
    console.error("Fetch briefs failed:", error);
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error("Network error - please check your connection");
    }
    if (error.name === 'AbortError') {
      throw new Error("Request timeout - server may be starting up");
    }
    throw error;
  }
}

export async function createBrief(sourceText, sessionId) {
  if (!sessionId) throw new Error("Session ID is required");
  if (!sourceText.trim()) throw new Error("Source text is required");
  
  console.log("Creating brief with session ID:", sessionId);
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
  
  const payload = {
    source_text: sourceText.trim(),
    client_session_id: sessionId,
  };
  
  console.log("Payload being sent:", payload);
  
  try {
    const res = await fetch(API_BASE, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error("API Error Response:", res.status, errorText);
      if (res.status >= 500) {
        throw new Error("Server error - please try again later");
      }
      if (res.status === 400) {
        throw new Error("Invalid input - please check your text");
      }
      throw new Error("Failed to create brief");
    }
    return await res.json();
  } catch (error) {
    clearTimeout(timeoutId);
    console.error("Create brief failed:", error);
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error("Network error - please check your connection");
    }
    if (error.name === 'AbortError') {
      throw new Error("Request timeout - server may be busy");
    }
    throw error;
  }
}

export async function getBrief(briefId, sessionId) {
  if (!briefId || !sessionId) throw new Error("Brief ID and Session ID are required");
  
  const res = await fetch(`${API_BASE}/${briefId}?client_session_id=${encodeURIComponent(sessionId)}`, {
    headers: {
      'Accept': 'application/json',
    }
  });
  if (!res.ok) throw new Error("Failed to fetch brief");
  return await res.json();
}

export async function deleteBrief(briefId, sessionId) {
  if (!briefId || !sessionId) throw new Error("Brief ID and Session ID are required");
  
  const res = await fetch(`${API_BASE}/${briefId}?client_session_id=${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 204) throw new Error("Failed to delete brief");
}