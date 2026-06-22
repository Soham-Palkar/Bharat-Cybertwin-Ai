import { useCyberStore } from '../../store/cyberStore';
import { Activity } from 'lucide-react';

export default function LiveFeed() {
  const { logs } = useCyberStore();
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Activity size={20} />
        Live Feed
      </h3>
      <div className="h-64 overflow-y-auto bg-bg rounded p-3 font-mono text-sm">
        {logs.length === 0 ? (
          <p className="text-textSecondary">Waiting for events...</p>
        ) : (
          logs.map(log => (
            <div key={log.event_id} className="mb-1">
              <span className="text-accent">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
              {log.asset_id && <span className="text-textSecondary">{log.asset_id}:</span>}{' '}
              {log.event_type}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
