import { create } from 'zustand';
import { Asset, Incident, RiskScore, LogEvent, ChatMessage, AskHuntGPTResponse, ContainmentAction, ContainmentActionType } from '../types';
import { fetchAssets, fetchIncidents, fetchRisk, askHuntGPT, containAsset, fetchContainmentHistory, getSnapshots, getInfrastructureChanges } from '../services/api';

interface CyberStore {
  // Data (existing)
  assets: Asset[];
  incidents: Incident[];
  riskScores: (RiskScore & { asset_name: string; asset_criticality: string })[];
  logs: LogEvent[];
  selectedAsset: Asset | null;
  loading: boolean;

  // HuntGPT
  chatHistory: ChatMessage[];
  huntgptLoading: boolean;
  copilotOpen: boolean;
  sendHuntGPTQuery: (query: string) => Promise<void>;
  clearChat: () => void;
  toggleCopilot: () => void;

  // Containment
  containmentHistory: ContainmentAction[];
  containmentLoading: boolean;
  executeContainment: (incidentId: string, actionType: ContainmentActionType, target: string) => Promise<void>;
  refreshContainmentHistory: () => Promise<void>;

  // Data Ingestion
  uploadStatus: string | null;
  recentUploads: any[];
  snapshots: any[];
  infrastructureChanges: { added: number; removed: number; modified: number; latestSnapshot: any | null };
  uploadAssets: (data: any, type: 'json' | 'csv') => Promise<void>;
  refreshPlatform: () => Promise<void>;

  // Actions (existing)
  fetchAllData: () => Promise<void>;
  setSelectedAsset: (asset: Asset | null) => void;
  addLog: (log: LogEvent) => void;
}

export const useCyberStore = create<CyberStore>((set, get) => ({
  // Initial state
  assets: [],
  incidents: [],
  riskScores: [],
  logs: [],
  selectedAsset: null,
  loading: true,

  // HuntGPT initial state
  chatHistory: [],
  huntgptLoading: false,
  copilotOpen: false,

  // Containment initial state
  containmentHistory: [],
  containmentLoading: false,

  // Data Ingestion initial state
  uploadStatus: null,
  recentUploads: [],
  snapshots: [],
  infrastructureChanges: { added: 0, removed: 0, modified: 0, latestSnapshot: null },

  // Fetch all data (existing)
  fetchAllData: async () => {
    try {
      set({ loading: true });
      const [assets, incidents, risk, containmentHistory, snapshots, infraChanges] = await Promise.all([
        fetchAssets(),
        fetchIncidents(),
        fetchRisk(),
        fetchContainmentHistory(),
        getSnapshots(),
        getInfrastructureChanges()
      ]);
      set({
        assets,
        incidents,
        riskScores: risk.assets,
        containmentHistory: containmentHistory.actions,
        snapshots: snapshots,
        infrastructureChanges: infraChanges,
        loading: false
      });
    } catch (err) {
      console.error(err);
      set({ loading: false });
    }
  },

  // UI actions (existing)
  setSelectedAsset: (asset) => set({ selectedAsset: asset }),
  addLog: (log) => set((state) => ({ logs: [log, ...state.logs.slice(0, 49)] })),

  // HuntGPT actions
  sendHuntGPTQuery: async (query) => {
    try {
      set({ huntgptLoading: true });
      // Add user message
      const userMsg: ChatMessage = { role: "user", content: query };
      set((state) => ({ chatHistory: [...state.chatHistory, userMsg] }));
      // Call API
      askHuntGPT(query).then((response) => {
        // Add assistant message
        const assistantMsg: ChatMessage = { role: "assistant", content: response.answer, data: response };
        set((state) => ({ chatHistory: [...state.chatHistory, assistantMsg], huntgptLoading: false }));
      }).catch(() => {
        set({ huntgptLoading: false });
      })
    } catch (err) {
      console.error(err);
      set({ huntgptLoading: false });
    }
  },
  clearChat: () => set({ chatHistory: [] }),
  toggleCopilot: () => set((state) => ({ copilotOpen: !state.copilotOpen })),

  // Containment actions
  executeContainment: async (incidentId, actionType, target) => {
    try {
      set({ containmentLoading: true });
      await containAsset(incidentId, actionType, target);
      await get().refreshContainmentHistory();
      set({ containmentLoading: false });
    } catch (err) {
      console.error(err);
      set({ containmentLoading: false });
    }
  },
  refreshContainmentHistory: async () => {
    try {
      const history = await fetchContainmentHistory();
      set({ containmentHistory: history.actions });
    } catch (err) {
      console.error(err);
    }
  },

  // Data Ingestion actions
  uploadAssets: async (data, type) => {
    try {
      set({ uploadStatus: 'Uploading assets...' });
      if (type === 'csv') {
        const form = new FormData();
        form.append('file', data);
        const res = await fetch('/api/upload-assets', {
          method: 'POST',
          body: form
        });
        const result = await res.json();
        if (result.status === 'success') {
          set({ uploadStatus: 'Assets uploaded successfully!', recentUploads: [result, ...get().recentUploads] });
          await get().refreshPlatform();
        }
      } else {
        const res = await fetch('/api/upload-assets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ assets: data })
        });
        const result = await res.json();
        if (result.status === 'success') {
          set({ uploadStatus: 'Assets uploaded successfully!', recentUploads: [result, ...get().recentUploads] });
          await get().refreshPlatform();
        }
      }
    } catch (err) {
      console.error(err);
      set({ uploadStatus: 'Failed to upload assets' });
    }
  },
  refreshPlatform: async () => {
    try {
      const [assets, incidents, risk, snapshots, infraChanges] = await Promise.all([
        fetchAssets(),
        fetchIncidents(),
        fetchRisk(),
        getSnapshots(),
        getInfrastructureChanges()
      ]);
      set({
        assets,
        incidents,
        riskScores: risk.assets,
        snapshots: snapshots,
        infrastructureChanges: infraChanges
      });
    } catch (err) {
      console.error(err);
    }
  }
}));
