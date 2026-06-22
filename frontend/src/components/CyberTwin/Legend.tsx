export default function Legend() {
  const items = [
    { color: '#22C55E', label: 'Low Risk' },
    { color: '#FACC15', label: 'Medium Risk' },
    { color: '#FB923C', label: 'High Risk' },
    { color: '#EF4444', label: 'Critical Risk' },
  ];

  return (
    <div className="absolute bottom-4 left-4 bg-card border border-border rounded-lg p-4 z-10">
      <h4 className="font-semibold mb-2">Risk Severity</h4>
      <div className="flex flex-col gap-2">
        {items.map(item => (
          <div key={item.label} className="flex items-center gap-2">
            <div 
              className="w-4 h-4 rounded" 
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
