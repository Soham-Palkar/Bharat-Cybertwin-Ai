import { Link, useLocation } from 'react-router-dom';
import { Shield, Activity, ShieldAlert } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-card border-b border-border px-6 py-4 flex items-center gap-8">
      <div className="flex items-center gap-2">
        <Shield className="text-accent w-8 h-8" />
        <h1 className="text-2xl font-bold">CyberTwin AI</h1>
      </div>
      
      <div className="flex gap-4">
        <Link 
          to="/dashboard" 
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition ${
            isActive('/dashboard') || isActive('/') 
              ? 'bg-accent/20 text-accent' 
              : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <Activity size={20} />
          <span>Dashboard</span>
        </Link>
        
        <Link 
          to="/cybertwin" 
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition ${
            isActive('/cybertwin') 
              ? 'bg-accent/20 text-accent' 
              : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <Shield size={20} />
          <span>CyberTwin</span>
        </Link>
        <Link 
          to="/containment" 
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition ${
            isActive('/containment') 
              ? 'bg-accent/20 text-accent' 
              : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <ShieldAlert size={20} />
          <span>Containment</span>
        </Link>
      </div>
    </nav>
  );
}
