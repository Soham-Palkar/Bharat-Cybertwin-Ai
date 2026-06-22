import { useEffect } from 'react';
import { useCyberStore } from '../store/cyberStore';
import { connectWebSocket } from '../services/websocket';
import AssetGraph from '../components/CyberTwin/AssetGraph';
import AssetDrawer from '../components/CyberTwin/AssetDrawer';
import Legend from '../components/CyberTwin/Legend';

export default function CyberTwinPage() {
  const { fetchAllData } = useCyberStore();

  useEffect(() => {
    fetchAllData();
    connectWebSocket();
    const interval = setInterval(() => fetchAllData(), 15000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  return (
    <div className="relative">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">CyberTwin Visualization</h2>
      </div>
      <AssetGraph />
      <Legend />
      <AssetDrawer />
    </div>
  );
}
