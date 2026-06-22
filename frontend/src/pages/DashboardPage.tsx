import { useEffect } from 'react';
import { useCyberStore } from '../store/cyberStore';
import { connectWebSocket } from '../services/websocket';
import { ShieldAlert, Server, AlertTriangle, TrendingUp } from 'lucide-react';
import KPICard from '../components/Dashboard/KPICard';
import RiskDistribution from '../components/Charts/RiskDistribution';
import TopRiskAssets from '../components/Dashboard/TopRiskAssets';
import LiveFeed from '../components/Dashboard/LiveFeed';
import IncidentTable from '../components/Dashboard/IncidentTable';
import DataIngestionCard from '../components/Dashboard/DataIngestionCard';
import InfrastructureChanges from '../components/Dashboard/InfrastructureChanges';

export default function DashboardPage() {
  const { 
    assets, 
    incidents, 
    riskScores, 
    fetchAllData 
  } = useCyberStore();
  
  const openIncidents = incidents.filter(i => i.status === 'open');
  const criticalAssets = assets.filter(a => a.criticality === 'Critical');
  
  // Calculate overall risk (weighted average)
  const criticalityWeight = { Low: 1, Medium: 2, High: 3, Critical: 4 };
  const weightedSum = riskScores.reduce((sum, rs) => sum + rs.total_score * (criticalityWeight[rs.asset_criticality as keyof typeof criticalityWeight] || 1), 0);
  const totalWeight = riskScores.reduce((sum, rs) => sum + (criticalityWeight[rs.asset_criticality as keyof typeof criticalityWeight] || 1), 0);
  const overallRisk = totalWeight > 0 ? (weightedSum / totalWeight).toFixed(1) : '0.0';
  
  useEffect(() => {
    fetchAllData();
    connectWebSocket();
    const interval = setInterval(() => fetchAllData(), 15000);
    return () => clearInterval(interval);
  }, [fetchAllData]);
  
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Executive Dashboard</h2>
      
      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPICard 
          title="Total Assets" 
          value={assets.length} 
          icon={<Server size={24} className="text-accent" />}
          colorClass="bg-accent/20"
        />
        <KPICard 
          title="Open Incidents" 
          value={openIncidents.length} 
          icon={<ShieldAlert size={24} className="text-critical" />}
          colorClass="bg-critical/20"
        />
        <KPICard 
          title="Critical Assets" 
          value={criticalAssets.length} 
          icon={<AlertTriangle size={24} className="text-high" />}
          colorClass="bg-high/20"
        />
        <KPICard 
          title="Overall Risk" 
          value={overallRisk} 
          icon={<TrendingUp size={24} className="text-accent" />}
          colorClass="bg-accent/20"
        />
      </div>
      
      {/* First Row */}
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-4 mb-6">
        <RiskDistribution />
      </div>
      
      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <InfrastructureChanges />
        <div className="lg:col-span-2">
          <TopRiskAssets />
        </div>
      </div>

      {/* Third Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <DataIngestionCard />
        <div className="lg:col-span-2">
          <LiveFeed />
        </div>
      </div>

      {/* Fourth Row */}
      <div className="grid grid-cols-1">
        <IncidentTable />
      </div>
    </div>
  );
}
