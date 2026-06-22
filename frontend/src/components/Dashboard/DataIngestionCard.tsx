import React, { useState } from 'react';
import { Upload, Database, AlertCircle } from 'lucide-react';
import { useCyberStore } from '../../store/cyberStore';

export default function DataIngestionCard() {
  const [activeTab, setActiveTab] = useState<'assets' | 'events' | 'dataset'>('assets');
  const [dragOver, setDragOver] = useState(false);
  const { uploadAssets, uploadStatus } = useCyberStore();

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (activeTab === 'assets') uploadAssets(file, 'csv');
    }
  };

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <h3 className="text-lg font-semibold text-slate-100 mb-4">Data Ingestion</h3>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {(['assets', 'events', 'dataset'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-cyan-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Upload area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files?.[0];
          if (file) {
            if (activeTab === 'assets') uploadAssets(file, 'csv');
          }
        }}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-all ${
          dragOver ? 'border-cyan-500 bg-cyan-500/10' : 'border-slate-600 bg-slate-800/50'
        }`}
      >
        <Upload className="w-10 h-10 mx-auto mb-3 text-slate-400" />
        <p className="text-slate-300 mb-2">
          Drop your {activeTab} file here or click to browse
        </p>
        <label className="cursor-pointer inline-block px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg transition-colors">
          Select File
          <input type="file" className="hidden" accept=".csv,.json" onChange={handleFile} />
        </label>
      </div>

      {uploadStatus && (
        <div className="mt-4 flex items-center gap-2 text-sm">
          {uploadStatus.includes('success') ? (
            <Database className="w-4 h-4 text-green-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-yellow-400" />
          )}
          <span className={uploadStatus.includes('success') ? 'text-green-300' : 'text-yellow-300'}>
            {uploadStatus}
          </span>
        </div>
      )}
    </div>
  );
}
