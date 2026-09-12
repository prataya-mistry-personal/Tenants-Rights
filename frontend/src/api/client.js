/**
 * API client to communicate with the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error('API health check error:', err);
    return { status: 'offline', faiss_loaded: false, total_chunks: 0, llm_model: 'unknown' };
  }
}

export async function fetchSources() {
  try {
    const res = await fetch(`${API_BASE}/sources`);
    if (!res.ok) throw new Error(`Failed to load sources: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error('Fetch sources error:', err);
    return { statutes: [], judgments: [], total_statutes: 0, total_judgments: 0 };
  }
}

export async function askQuestion(question, jurisdiction = 'Bengaluru', topK = 4) {
  const payload = {
    question: question.trim(),
    jurisdiction: jurisdiction || null,
    top_k: topK,
  };

  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Server error (${res.status})`);
  }

  return await res.json();
}
