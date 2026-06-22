import { useCyberStore } from '../../store/cyberStore';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'Critical': return 'bg-critical/20 text-critical border-critical';
    case 'High': return 'bg-high/20 text-high border-high';
    case 'Medium': return 'bg-medium/20 text-medium border-medium';
    default: return 'bg-low/20 text-low border-low';
  }
}

export default function AssetDrawer() {
  const { selectedAsset, setSelectedAsset, incidents, riskScores } = useCyberStore();
  
  if (!selectedAsset) return null;

  const assetRisk = riskScores.find(r => r.asset_id === selectedAsset.asset_id);
  const assetIncidents = incidents.filter(i => i.related_asset_id === selectedAsset.asset_id);

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-card border-l border-border shadow-2xl z-50 p-6 overflow-y-auto">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold">{selectedAsset.name}</h2>
          <p className="text-textSecondary text-sm">{selectedAsset.asset_id}</p>
        </div>
        <button 
          onClick={() => setSelectedAsset(null)}
          className="text-textSecondary hover:text-textPrimary"
        >
          <X size={24} />
        </button>
      </div>

      <div className="space-y-6">
        {/* Basic Info */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Asset Details</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-textSecondary">Type</p>
              <p className="font-medium capitalize">{selectedAsset.asset_type}</p>
            </div>
            <div>
              <p className="text-textSecondary">Criticality</p>
              <span className={clsx(
                'px-2 py-1 rounded text-xs border inline-block',
                getSeverityColor(selectedAsset.criticality)
              )}>
                {selectedAsset.criticality}
              </span>
            </div>
            {selectedAsset.ip_address && (
              <div>
                <p className="text-textSecondary">IP Address</p>
                <p className="font-medium">{selectedAsset.ip_address}</p>
              </div>
            )}
            {selectedAsset.owner && (
              <div>
                <p className="text-textSecondary">Owner</p>
                <p className="font-medium">{selectedAsset.owner}</p>
              </div>
            )}
          </div>
        </div>

        {/* Risk Score */}
        {assetRisk && (
          <div>
            <h3 className="text-lg font-semibold mb-3">Risk Breakdown</h3>
            <div className="bg-bg rounded p-4">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Rule Score</span>
                  <span className="font-medium">{assetRisk.rule_score.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>ML Score</span>
                  <span className="font-medium">{assetRisk.ml_score.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Criticality Weight</span>
                  <span className="font-medium">{assetRisk.criticality_weight}</span>
                </div>
                <div className="border-t border-border pt-2 mt-2">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold">Total Score</span>
                    <span className={clsx(
                      'text-2xl font-bold',
                      assetRisk.severity === 'Critical' ? 'text-critical' :
                      assetRisk.severity === 'High' ? 'text-high' :
                      assetRisk.severity === 'Medium' ? 'text-medium' : 'text-low'
                    )}>
                      {assetRisk.total_score.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Open Incidents */}
        <div>
          <h3 className="text-lg font-semibold mb-3">
            Open Incidents ({assetIncidents.filter(i => i.status === 'open').length})
          </h3>
          <div className="space-y-2">
            {assetIncidents.length === 0 ? (
              <p className="text-textSecondary text-sm">No incidents for this asset.</p>
            ) : (
              assetIncidents.map(incident => (
                <div key={incident.incident_id} className="bg-bg rounded p-3 border border-border">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sm">{incident.title}</p>
                      <p className="text-textSecondary text-xs">{incident.incident_id}</p>
                    </div>
                    <span className={clsx(
                      'px-2 py-1 rounded text-xs',
                      getSeverityColor(incident.severity)
                    )}>
                      {incident.severity}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
