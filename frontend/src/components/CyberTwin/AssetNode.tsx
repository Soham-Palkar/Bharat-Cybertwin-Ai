import { Handle, Position, NodeProps } from 'reactflow';
import { Server, Database, Lock, Monitor, ShieldAlert, HelpCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { AssetType, Criticality } from '../../types';

interface AssetNodeData {
  label: string;
  type: AssetType;
  criticality: Criticality;
}

function getIconForType(type: AssetType) {
  switch (type) {
    case 'server': return <Server size={24} />;
    case 'database': return <Database size={24} />;
    case 'vpn': return <Lock size={24} />;
    case 'endpoint': return <Monitor size={24} />;
    case 'firewall': return <ShieldAlert size={24} />;
    default: return <HelpCircle size={24} />;
  }
}

function getColorForSeverity(severity: Criticality) {
  switch (severity) {
    case 'Critical': return 'border-critical bg-critical/10';
    case 'High': return 'border-high bg-high/10';
    case 'Medium': return 'border-medium bg-medium/10';
    default: return 'border-low bg-low/10';
  }
}

export default function AssetNode({ data }: NodeProps<AssetNodeData>) {
  return (
    <div className={clsx(
      'rounded-lg border-2 p-3 bg-card shadow-lg min-w-[120px]',
      getColorForSeverity(data.criticality)
    )}>
      <Handle type="target" position={Position.Top} className="bg-accent" />
      <div className="flex flex-col items-center gap-1">
        {getIconForType(data.type)}
        <div className="text-xs font-medium text-center">{data.label}</div>
      </div>
      <Handle type="source" position={Position.Bottom} className="bg-accent" />
    </div>
  );
}
