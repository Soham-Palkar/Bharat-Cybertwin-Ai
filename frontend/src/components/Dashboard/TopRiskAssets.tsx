import { useCyberStore } from '../../store/cyberStore';
import { clsx } from 'clsx';

function getColorForSeverity(severity: string) {
  switch (severity) {
    case 'Critical': return 'bg-critical';
    case 'High': return 'bg-high';
    case 'Medium': return 'bg-medium';
    default: return 'bg-low';
  }
}

export default function TopRiskAssets() {
  const { riskScores } = useCyberStore();
  const top5 = [...riskScores].sort((a, b) => b.total_score - a.total_score).slice(0, 5);

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Top 5 Risk Assets</h3>
      <div className="space-y-4">
        {top5.map((asset, idx) => (
          <div key={asset.score_id}>
            <div className="flex justify-between mb-1">
              <span className="text-sm">{asset.asset_name}</span>
              <span className="text-sm font-medium">{asset.total_score.toFixed(1)}</span>
            </div>
            <div className="w-full bg-border rounded-full h-2.5">
              <div 
                className={clsx('h-2.5 rounded-full', getColorForSeverity(asset.severity))}
                style={{ width: `${Math.min(asset.total_score, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
