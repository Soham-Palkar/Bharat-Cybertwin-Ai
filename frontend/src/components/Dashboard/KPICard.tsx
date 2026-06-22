import { ReactNode } from 'react';

interface KPICardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  colorClass: string;
}

export default function KPICard({ title, value, icon, colorClass }: KPICardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-6 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${colorClass}`}>
        {icon}
      </div>
      <div>
        <p className="text-textSecondary text-sm">{title}</p>
        <p className="text-3xl font-bold">{value}</p>
      </div>
    </div>
  );
}
