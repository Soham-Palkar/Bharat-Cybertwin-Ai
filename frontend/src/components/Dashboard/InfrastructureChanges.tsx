import React from 'react';
import { Plus, Minus, RotateCw } from 'lucide-react';
import { useCyberStore } from '../../store/cyberStore';

export default function InfrastructureChanges() {
  const { infrastructureChanges } = useCyberStore();

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <h3 className="text-lg font-semibold text-slate-100 mb-4">Infrastructure Changes</h3>

      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Plus className="w-5 h-5 text-green-400" />
            <span className="text-2xl font-bold text-green-400">+{infrastructureChanges.added}</span>
          </div>
          <span className="text-xs text-slate-400 uppercase tracking-wider">Added</span>
        </div>

        <div className="text-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Minus className="w-5 h-5 text-red-400" />
            <span className="text-2xl font-bold text-red-400">-{infrastructureChanges.removed}</span>
          </div>
          <span className="text-xs text-slate-400 uppercase tracking-wider">Removed</span>
        </div>

        <div className="text-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="flex items-center justify-center gap-2 mb-2">
            <RotateCw className="w-5 h-5 text-yellow-400" />
            <span className="text-2xl font-bold text-yellow-400">~{infrastructureChanges.modified}</span>
          </div>
          <span className="text-xs text-slate-400 uppercase tracking-wider">Modified</span>
        </div>
      </div>

      {infrastructureChanges.latestSnapshot && (
        <div className="mt-4 pt-4 border-t border-slate-700 text-sm text-slate-400">
          Last snapshot: <span className="text-slate-200">{infrastructureChanges.latestSnapshot.filename}</span>
        </div>
      )}
    </div>
  );
}
