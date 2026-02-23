const BASE = '/api';

async function request(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const getFlows = () => request(`${BASE}/flows`);

export const getFlow = (flowId) => request(`${BASE}/flow/${flowId}`);

export const getStep = (flowId, stepId) =>
  request(`${BASE}/flow/${flowId}/step/${stepId}`);

export const submitStep = (flowId, stepId, choice) =>
  request(`${BASE}/flow/${flowId}/step/${stepId}/next`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ choice }),
  });

export const logSession = (sessionData) =>
  request(`${BASE}/log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sessionData),
  });
