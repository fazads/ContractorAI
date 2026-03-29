const API_BASE = import.meta.env.VITE_API_BASE_URL || window.location.origin || 'http://localhost:8000';

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || 'Request failed');
  }
  return payload;
}

export async function getSampleContract(kind = "default") {
  const response = await fetch(`${API_BASE}/api/sample-contract?kind=${encodeURIComponent(kind)}`);
  return parseResponse(response);
}

export async function analyzeText({ text, fileName, policyPack }) {
  const response = await fetch(`${API_BASE}/api/analyze-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, file_name: fileName, policy_pack: policyPack }),
  });
  return parseResponse(response);
}

export async function analyzeUpload({ file, policyPack }) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('policy_json', JSON.stringify(policyPack));
  const response = await fetch(`${API_BASE}/api/analyze-upload`, {
    method: 'POST',
    body: formData,
  });
  return parseResponse(response);
}

export async function askQuestion(contractId, question) {
  const response = await fetch(`${API_BASE}/api/contracts/${contractId}/question`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return parseResponse(response);
}

export async function reassessContract(contractId, policyPack) {
  const response = await fetch(`${API_BASE}/api/contracts/${contractId}/reassess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ policy_pack: policyPack }),
  });
  return parseResponse(response);
}
