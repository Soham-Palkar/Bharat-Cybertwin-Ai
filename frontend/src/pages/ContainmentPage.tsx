import React, { useEffect, useState } from 'react';
import { useCyberStore } from '../store/cyberStore';
import { ShieldAlert, ShieldCheck, ShieldX, Trash2, Lock, Unlock, UserX, RefreshCw, WifiOff } from 'lucide-react';
import { clsx } from 'clsx';
import { ContainmentActionType } from '../types';

const ACTIONS: { type: ContainmentActionType; label: string; color: string; icon: any }[] = [
  { type: "block_ip", label: "Block IP", color: "bg-red-500/10 text-red-400 border border-red-500/30", icon: WifiOff },
  { type: "disable_user", label: "Disable User", color: "bg-orange-500/10 text-orange-400 border border-orange-500/30", icon: UserX },
  { type: "force_mfa", label: "Force MFA", color: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30", icon: Lock },
  { type: "reset_password", label: "Reset Password", color: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30", icon: RefreshCw },
  { type: "quarantine", label: "Quarantine", color: "bg-pink-500/10 text-pink-400 border border-pink-500/30", icon: ShieldX }
];

function getSeverityColor(severity: string) {
  switch (severity) {
    case "Critical": return "bg-red-500/10 text-red-400 border border-red-500/30";
    case "High": return "bg-orange-500/10 text-orange-400 border border-orange-500/30";
    case "Medium": return "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30";
    default: return "bg-green-500/10 text-green-400 border border-green-500/30";
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case "open": return "bg-red-500/10 text-red-400 border border-red-500/30";
    case "investigating": return "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30";
    case "contained": return "bg-blue-500/10 text-blue-400 border border-blue-500/30";
    case "closed": return "bg-green-500/10 text-green-400 border border-green-500/30";
    default: return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
  }
}

function getContainmentStatusColor(status: string) {
  switch (status) {
    case "pending": return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
    case "executing": return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 animate-pulse";
    case "simulated_success": return "bg-green-500/10 text-green-400 border border-green-500/30";
    case "failed": return "bg-red-500/10 text-red-400 border border-red-500/30";
    default: return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
  }
}

export default function ContainmentPage() {
  const {
    assets,
    incidents,
    containmentHistory,
    containmentLoading,
    executeContainment,
    fetchAllData
  } = useCyberStore();

  const [targetValue, setTargetValue] = useState<string>("");
  const [selectedAction, setSelectedAction] = useState<ContainmentActionType>("force_mfa");
  const [confirmModal, setConfirmModal] = useState<{ incidentId: string; target: string; actionType: ContainmentActionType } | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // Only show open or investigating incidents
  const activeIncidents = incidents.filter(i => i.status !== "closed");

  const getAssetName = (assetId?: string) => {
    if (!assetId) return "Unknown Asset";
    const asset = assets.find(a => a.asset_id === assetId);
    return asset?.name ?? assetId;
  };

  const getAssetIP = (assetId?: string) => {
    if (!assetId) return "0.0.0.0";
    const asset = assets.find(a => a.asset_id === assetId);
    return asset?.ip_address ?? "0.0.0.0";
  };

  const extractUserFromDescription = (desc?: string) => {
    const match = desc?.match(/User ['"](\S+)['"]/i) || desc?.match(/for (\S+)/i);
    return match ? match[1] : "admin";
  };

  const handleExecute = (incidentId: string, target: string, actionType: ContainmentActionType) => {
    setConfirmModal({ incidentId, target, actionType });
  };

  const confirmExecute = async () => {
    if (!confirmModal) return;
    try {
      await executeContainment(confirmModal.incidentId, confirmModal.actionType, confirmModal.target);
      setToast(`Successfully executed ${confirmModal.actionType} on ${confirmModal.target}`);
    } catch (e) {
      setToast(`Failed to execute ${confirmModal.actionType}`);
    } finally {
      setConfirmModal(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Containment Center</h2>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 rounded text-sm">
            <ShieldAlert size={16} className="inline mr-1" />
            Simulated Mode
          </span>
        </div>
      </div>

      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-24 right-6 z-40 bg-slate-800 border border-slate-700 shadow-lg rounded-lg p-4 flex items-center gap-3">
          <ShieldCheck className="text-green-400" size={20} />
          <span className="text-sm">{toast}</span>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg max-w-md w-11/12 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold flex items-center gap-2">
                <ShieldAlert className="text-orange-400" size={24} />
                Confirm Containment Action
              </h3>
              <button onClick={() => setConfirmModal(null)} className="text-slate-400 hover:text-slate-200">
                <Trash2 size={20} />
              </button>
            </div>
            <div className="space-y-4 mb-6">
              <p className="text-slate-300">
                You are about to execute <span className="font-bold text-cyan-400">{confirmModal.actionType}</span> on <span className="font-bold text-cyan-400">{confirmModal.target}</span> for incident {confirmModal.incidentId}.
              </p>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-3 text-xs text-yellow-300 flex items-start gap-2">
                <ShieldAlert size={16} className="mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-bold">WARNING</p>
                  <p>This is a simulated action only. No real infrastructure will be affected.</p>
                </div>
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmModal(null)}
                className="px-4 py-2 rounded border border-slate-600 text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={confirmExecute}
                disabled={containmentLoading}
                className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {containmentLoading ? "Executing..." : "Execute Action"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main table - 2/3 width */}
        <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-slate-700 flex justify-between items-center">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <ShieldAlert size={20} className="text-orange-400" />
              Active Incidents Requiring Containment
            </h3>
            <span className="text-xs text-slate-400">
              {activeIncidents.length} active
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="text-slate-400 border-b border-slate-700 bg-slate-900/50">
                <tr>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Incident</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Asset</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Severity</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {activeIncidents.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-12 text-center text-slate-500">
                    <ShieldCheck size={48} className="mx-auto mb-3 text-slate-600" />
                    <p>No active incidents. Great job!</p>
                  </td></tr>
                ) : activeIncidents.map((incident) => (
                  <tr key={incident.incident_id} className="hover:bg-slate-700/30 transition">
                    <td className="px-4 py-4">
                      <div className="font-medium text-slate-200">{incident.title}</div>
                      <div className="text-xs text-slate-500 mt-1 line-clamp-2">{incident.description}</div>
                      <div className="text-[10px] text-slate-600 mt-1 font-mono">{incident.incident_id}</div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm text-slate-200">{getAssetName(incident.related_asset_id)}</div>
                      <div className="text-xs text-slate-500 font-mono">{getAssetIP(incident.related_asset_id)}</div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={clsx("px-2 py-1 rounded-full text-xs border", getSeverityColor(incident.severity))}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className={clsx("px-2 py-1 rounded-full text-xs border capitalize", getStatusColor(incident.status))}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap gap-2">
                        {/* Pre-populate target based on incident */}
                        <button
                          onClick={() => handleExecute(incident.incident_id, getAssetIP(incident.related_asset_id), "block_ip")}
                          className="px-2.5 py-1.5 rounded text-xs flex items-center gap-1 hover:scale-105 transition border border-red-500/30 text-red-400 bg-red-500/10"
                        >
                          <WifiOff size={12} />
                          Block IP
                        </button>
                        <button
                          onClick={() => handleExecute(incident.incident_id, extractUserFromDescription(incident.description), "disable_user")}
                          className="px-2.5 py-1.5 rounded text-xs flex items-center gap-1 hover:scale-105 transition border border-orange-500/30 text-orange-400 bg-orange-500/10"
                        >
                          <UserX size={12} />
                          Disable User
                        </button>
                        <button
                          onClick={() => handleExecute(incident.incident_id, getAssetName(incident.related_asset_id), "quarantine")}
                          className="px-2.5 py-1.5 rounded text-xs flex items-center gap-1 hover:scale-105 transition border border-pink-500/30 text-pink-400 bg-pink-500/10"
                        >
                          <ShieldX size={12} />
                          Quarantine
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sidebar: Containment History */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-lg font-semibold">Recent Containment Actions</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[600px]">
            {containmentHistory.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <ShieldCheck size={40} className="mx-auto mb-3 opacity-50" />
                <p className="text-sm">No containment actions yet</p>
              </div>
            ) : [...containmentHistory].reverse().map((action) => (
              <div key={action.action_id} className="bg-slate-900/50 rounded p-3 border border-slate-700 hover:border-slate-600 transition">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold font-mono text-slate-300">{action.action_id}</div>
                  <span className={clsx("text-[10px] px-2 py-0.5 rounded-full border", 
                    ACTIONS.find(a => a.type === action.action_type)?.color
                  )}>
                    {action.action_type.replace("_", " ")}
                  </span>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Target:</span>
                    <span className="text-slate-300 font-mono">{action.target}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Incident:</span>
                    <span className="text-slate-300 font-mono">{action.incident_id}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Executed:</span>
                    <span className="text-slate-300">{new Date(action.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 pt-1 border-t border-slate-800">
                    <span className="text-slate-500">Status:</span>
                    <span className={clsx("text-xs font-semibold flex items-center gap-1 px-2 py-0.5 rounded-full border", 
                      getContainmentStatusColor(action.status)
                    )}>
                      {action.status === "simulated_success" && <ShieldCheck size={12} />}
                      {action.status === "pending" && "Pending..."}
                      {action.status === "executing" && "Executing..."}
                      {action.status === "simulated_success" && "Simulated Success"}
                      {action.status === "failed" && "Failed"}
                    </span>
                  </div>
                  {action.note && (
                    <div className="mt-2 text-xs text-slate-400 border-t border-slate-800 pt-1">
                      {action.note}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
