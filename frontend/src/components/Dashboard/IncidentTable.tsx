import { useCyberStore } from '../../store/cyberStore';
import { clsx } from 'clsx';

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'Critical': return 'bg-critical/20 text-critical';
    case 'High': return 'bg-high/20 text-high';
    case 'Medium': return 'bg-medium/20 text-medium';
    default: return 'bg-low/20 text-low';
  }
}

export default function IncidentTable() {
  const { incidents } = useCyberStore();
  
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Incidents</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-textSecondary uppercase">
            <tr>
              <th className="pb-3 pr-6">Incident ID</th>
              <th className="pb-3 pr-6">Asset</th>
              <th className="pb-3 pr-6">Title</th>
              <th className="pb-3 pr-6">Severity</th>
              <th className="pb-3 pr-6">Status</th>
              <th className="pb-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map(incident => (
              <tr key={incident.incident_id} className="border-t border-border">
                <td className="py-3 pr-6">{incident.incident_id}</td>
                <td className="py-3 pr-6">{incident.related_asset_id || 'N/A'}</td>
                <td className="py-3 pr-6">{incident.title}</td>
                <td className="py-3 pr-6">
                  <span className={clsx('px-2 py-1 rounded text-xs', getSeverityColor(incident.severity))}>
                    {incident.severity}
                  </span>
                </td>
                <td className="py-3 pr-6 capitalize">{incident.status}</td>
                <td className="py-3">
                  {new Date(incident.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
