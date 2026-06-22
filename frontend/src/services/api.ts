import { Asset, Incident, RiskScore, MlAnomaly, AskHuntGPTResponse, ContainmentAction, ContainmentActionType } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export async function fetchAssets(): Promise<Asset[]> {
  const res = await fetch(`${API_BASE}/assets`);
  if (!res.ok) throw new Error('Failed to fetch assets');
  return res.json();
}

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch(`${API_BASE}/incidents`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchRisk(): Promise<{ asset_count: number; assets: (RiskScore & { asset_name: string; asset_criticality: string })[] }> {
  const res = await fetch(`${API_BASE}/risk`);
  if (!res.ok) throw new Error('Failed to fetch risk scores');
  return res.json();
}

export async function fetchMlAnomalies(): Promise<{ asset_count: number; assets: MlAnomaly[] }> {
  const res = await fetch(`${API_BASE}/ml/anomalies`);
  if (!res.ok) throw new Error('Failed to fetch ML anomalies');
  return res.json();
}

export async function askHuntGPT(query: string): Promise<AskHuntGPTResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!res.ok) throw new Error('Failed to get HuntGPT response');
  return res.json();
}

export async function containAsset(incidentId: string, actionType: ContainmentActionType, target: string): Promise<{ status: string; action_id: string; note: string }> {
  const res = await fetch(`${API_BASE}/contain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId, action_type: actionType, target })
  });
  if (!res.ok) throw new Error('Failed to execute containment action');
  return res.json();
}

export async function fetchContainmentHistory(): Promise<{ actions: ContainmentAction[] }> {
  const res = await fetch(`${API_BASE}/containment-history`);
  if (!res.ok) throw new Error('Failed to fetch containment history');
  return res.json();
}

export async function uploadEvents(data: any): Promise<any> {
  if (data instanceof File) {
    const form = new FormData();
    form.append('file', data);
    const res = await fetch(`${API_BASE}/upload-events`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Failed to upload events');
    return res.json();
  }
  const res = await fetch(`${API_BASE}/upload-events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ events: data })
  });
  if (!res.ok) throw new Error('Failed to upload events');
  return res.json();
}

export async function uploadDataset(file: File): Promise<any> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/upload-dataset`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Failed to upload dataset');
  return res.json();
}

export async function getSnapshots(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/snapshots`);
  if (!res.ok) throw new Error('Failed to fetch snapshots');
  return res.json();
}

export async function getInfrastructureChanges(): Promise<{ added: number; removed: number; modified: number; latestSnapshot: any | null }> {
  const res = await fetch(`${API_BASE}/infrastructure-changes`);
  if (!res.ok) throw new Error('Failed to fetch infrastructure changes');
  return res.json();
}

