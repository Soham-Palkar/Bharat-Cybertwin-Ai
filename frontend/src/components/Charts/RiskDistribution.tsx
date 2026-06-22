import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useCyberStore } from '../../store/cyberStore';

export default function RiskDistribution() {
  const { riskScores } = useCyberStore();
  const data = riskScores.slice(0, 10).map(rs => ({
    name: rs.asset_name,
    risk: rs.total_score
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Risk Distribution</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94A3B8" />
            <YAxis stroke="#94A3B8" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F1F5F9' }}
            />
            <Bar dataKey="risk" fill="#06B6D4" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
