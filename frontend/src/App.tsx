import { useState } from 'react';
import { LayoutDashboard, Map, Shield } from 'lucide-react';
import Dashboard from './components/Dashboard';
import RiskMap from './components/RiskMap';
import RiskIntelligence from './components/RiskIntelligence';

type View = 'dashboard' | 'map' | 'intelligence';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const navItems = [
    { id: 'dashboard' as View, label: 'Overview', icon: LayoutDashboard },
    { id: 'map' as View, label: 'Supply Map', icon: Map },
    { id: 'intelligence' as View, label: 'Risk Intelligence', icon: Shield },
  ];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">ATLAS</div>
        <div className="sidebar-subtitle">Intelligence System</div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${currentView === item.id ? 'active' : ''}`}
              onClick={() => setCurrentView(item.id)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content — CSS display:none to prevent unmounting */}
      <main className="main-content">
        <div style={{ display: currentView === 'dashboard' ? 'block' : 'none' }}>
          <Dashboard />
        </div>
        <div style={{ display: currentView === 'map' ? 'block' : 'none' }}>
          <RiskMap />
        </div>
        <div style={{ display: currentView === 'intelligence' ? 'block' : 'none' }}>
          <RiskIntelligence />
        </div>
      </main>
    </div>
  );
}

export default App;