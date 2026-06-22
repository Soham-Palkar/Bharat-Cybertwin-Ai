import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const mockData = [
  { name: 'Mon', incidents: 3 },
  { name: 'Tue', incidents: 5 },
  { name: 'Wed', incidents: 2 },
  { name: 'Thu', incidents: 7 },
  { name: 'Fri', incidents: 4 },
  { name: 'Sat', incidents: 1 },
  { name: 'Sun', incidents: 3 },
];

export default function IncidentTimeline() {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Incident Timeline</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={mockData}>
            <defs>
              <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#06B6D4" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94A3B8" />
            <YAxis stroke="#94A3B8" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F1F5F9' }}
              itemStyle={{ color: '#F1F5F9' }}
            />
            <Area type="monotone" dataKey="incidents" stroke="#06B6D4" fillOpacity={1} fill="url(#colorIncidents)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
