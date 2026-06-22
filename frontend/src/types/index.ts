export type AssetType = "server" | "database" | "vpn" | "endpoint" | "firewall" | "unknown";
export type Criticality = "Low" | "Medium" | "High" | "Critical";
export type IncidentSeverity = "Low" | "Medium" | "High" | "Critical";
export type IncidentStatus = "open" | "investigating" | "contained" | "closed";

export interface Asset {
  asset_id: string;
  name: string;
  asset_type: AssetType;
  ip_address?: string;
  criticality: Criticality;
  owner?: string;
  created_at: string;
}

export interface Incident {
  incident_id: string;
  title: string;
  description?: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  related_asset_id?: string;
  created_at: string;
}

export interface RiskScore {
  score_id: string;
  asset_id: string;
  rule_score: number;
  ml_score: number;
  criticality_weight: number;
  total_score: number;
  severity: Criticality;
  computed_at: string;
}

export interface LogEvent {
  event_id: string;
  asset_id?: string;
  source_ip?: string;
  event_type: string;
  raw_payload?: string;
  timestamp: string;
}

export interface MlAnomaly {
  asset_id: string;
  anomaly_score: number;
  threat_confidence: number;
  threat_probability: number;
}

export interface MitreItem {
  id: string;
  name: string;
}

export interface AssetReference {
  asset_id: string;
  name: string;
  risk_score?: number;
}

export interface IncidentReference {
  incident_id: string;
  title: string;
}

export interface AskHuntGPTResponse {
  answer: string;
  mitre: MitreItem[];
  assets: AssetReference[];
  incidents: IncidentReference[];
  recommendations: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  data?: AskHuntGPTResponse;
}

export interface ContainmentAction {
  action_id: string;
  incident_id: string;
  action_type: string;
  target: string;
  status: string;
  note?: string;
  created_at: string;
}

export type ContainmentActionType = "block_ip" | "disable_user" | "force_mfa" | "reset_password" | "quarantine";
