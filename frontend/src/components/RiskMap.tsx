import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RefreshCw } from 'lucide-react';

// Fix default marker icons for Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const API_BASE = 'http://localhost:8000/api/v1';

interface Port {
  id: string;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  risk_level: string;
  risk_score: number;
  status: string;
}

// Chokepoint locations
const CHOKEPOINTS = [
  { name: 'Suez Canal', lat: 30.4574, lon: 32.3499, region: 'Egypt' },
  { name: 'Panama Canal', lat: 9.0800, lon: -79.6800, region: 'Panama' },
  { name: 'Strait of Hormuz', lat: 26.5667, lon: 56.2500, region: 'Iran/Oman' },
  { name: 'Strait of Malacca', lat: 2.5000, lon: 101.2000, region: 'Malaysia/Indonesia' },
  { name: 'Bosphorus Strait', lat: 41.1190, lon: 29.0510, region: 'Turkey' },
  { name: 'Bab el-Mandeb Strait', lat: 12.5833, lon: 43.3333, region: 'Yemen/Djibouti' },
];

// Major trade routes as polyline coordinates
const TRADE_ROUTES: { name: string; color: string; positions: [number, number][] }[] = [
  {
    name: 'Asia → Europe (via Suez)',
    color: '#3b82f6',
    positions: [
      [1.26, 103.82],    // Singapore
      [2.50, 101.20],    // Malacca
      [12.58, 43.33],    // Bab el-Mandeb
      [30.46, 32.35],    // Suez
      [35.90, -5.30],    // Gibraltar
      [51.90, 4.49],     // Rotterdam
    ],
  },
  {
    name: 'Asia → Americas (via Panama)',
    color: '#10b981',
    positions: [
      [31.36, 121.51],   // Shanghai
      [35.10, 129.04],   // Busan
      [21.30, -157.86],  // Hawaii
      [9.08, -79.68],    // Panama
      [33.74, -118.26],  // Los Angeles
    ],
  },
  {
    name: 'Middle East → Asia (via Hormuz)',
    color: '#f59e0b',
    positions: [
      [25.01, 55.06],    // Dubai
      [26.57, 56.25],    // Hormuz
      [18.95, 72.95],    // Mumbai
      [2.50, 101.20],    // Malacca
      [1.26, 103.82],    // Singapore
    ],
  },
  {
    name: 'Black Sea → Mediterranean (via Bosphorus)',
    color: '#8b5cf6',
    positions: [
      [46.48, 30.74],    // Odessa
      [41.12, 29.05],    // Bosphorus
      [37.94, 23.64],    // Athens
      [35.90, -5.30],    // Gibraltar
      [53.55, 9.97],     // Hamburg
    ],
  },
];

function riskColor(level: string): string {
  switch (level) {
    case 'critical': return '#ef4444';
    case 'high': return '#f59e0b';
    case 'medium': return '#3b82f6';
    default: return '#10b981';
  }
}

function riskRadius(level: string): number {
  switch (level) {
    case 'critical': return 10;
    case 'high': return 8;
    case 'medium': return 7;
    default: return 6;
  }
}

// Custom chokepoint icon
function createChokepointIcon() {
  return L.divIcon({
    className: 'chokepoint-marker',
    html: `<div style="
      width: 20px;
      height: 20px;
      background: rgba(239, 68, 68, 0.8);
      border: 2px solid #fff;
      border-radius: 4px;
      transform: rotate(45deg);
      box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

// Legend component
function MapLegend() {
  const map = useMap();

  useEffect(() => {
    const legend = new L.Control({ position: 'bottomright' });

    legend.onAdd = function () {
      const div = L.DomUtil.create('div', 'map-legend');
      div.innerHTML = `
        <div style="
          background: rgba(17, 24, 39, 0.95);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          padding: 12px 16px;
          color: #e2e8f0;
          font-size: 12px;
          min-width: 160px;
        ">
          <div style="font-weight: 700; margin-bottom: 8px; font-size: 13px;">Legend</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:12px;height:12px;border-radius:50%;background:#ef4444;display:inline-block"></span> Critical Risk
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:12px;height:12px;border-radius:50%;background:#f59e0b;display:inline-block"></span> High Risk
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:12px;height:12px;border-radius:50%;background:#3b82f6;display:inline-block"></span> Medium Risk
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span style="width:12px;height:12px;border-radius:50%;background:#10b981;display:inline-block"></span> Low Risk
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span style="width:12px;height:12px;background:#ef4444;transform:rotate(45deg);display:inline-block;border:1px solid white;border-radius:2px"></span> Chokepoint
          </div>
          <div style="border-top:1px solid rgba(255,255,255,0.1);margin-top:8px;padding-top:8px;font-size:11px;color:#94a3b8">
            Lines = Trade Routes
          </div>
        </div>
      `;
      return div;
    };

    legend.addTo(map);
    return () => {
      legend.remove();
    };
  }, [map]);

  return null;
}

export default function RiskMap() {
  const [ports, setPorts] = useState<Port[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRoutes, setShowRoutes] = useState(true);

  useEffect(() => {
    fetchPorts();
  }, []);

  async function fetchPorts() {
    try {
      const res = await fetch(`${API_BASE}/risk/ports`);
      const data = await res.json();
      setPorts(data.ports || []);
    } catch (e) {
      console.error('Ports fetch error:', e);
    }
    setLoading(false);
  }

  return (
    <div>
      <div className="section-header" style={{ marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>Global Supply Chain Map</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            Live vessel tracking, port risk levels, chokepoints, and trade routes
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className={`btn ${showRoutes ? 'btn-primary' : ''}`}
            onClick={() => setShowRoutes(!showRoutes)}
          >
            {showRoutes ? 'Hide Routes' : 'Show Routes'}
          </button>
          <button className="btn" onClick={() => { setLoading(true); fetchPorts(); }}>
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </div>

      {/* MAP */}
      <div style={{
        borderRadius: 12,
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
        marginBottom: 24,
        height: '600px',
      }}>
        <MapContainer
          center={[20, 40]}
          zoom={2.5}
          style={{ height: '100%', width: '100%', background: '#0a0e17' }}
          scrollWheelZoom={true}
          zoomControl={true}
          minZoom={2}
          maxZoom={12}
        >
          {/* Dark map tiles */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />

          {/* Trade Routes */}
          {showRoutes && TRADE_ROUTES.map((route, i) => (
            <Polyline
              key={i}
              positions={route.positions}
              pathOptions={{
                color: route.color,
                weight: 2,
                opacity: 0.6,
                dashArray: '8 6',
              }}
            >
              <Popup>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{route.name}</div>
              </Popup>
            </Polyline>
          ))}

          {/* Port Markers */}
          {ports.map((port) => (
            <CircleMarker
              key={port.id}
              center={[port.latitude, port.longitude]}
              radius={riskRadius(port.risk_level)}
              pathOptions={{
                fillColor: riskColor(port.risk_level),
                fillOpacity: 0.8,
                color: '#ffffff',
                weight: 2,
                opacity: 0.9,
              }}
            >
              <Popup>
                <div style={{ minWidth: 200 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>
                    {port.name}
                  </div>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                    {port.country}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Risk Score:</span>
                    <span style={{ fontWeight: 700, color: riskColor(port.risk_level) }}>
                      {port.risk_score}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Level:</span>
                    <span style={{
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      color: riskColor(port.risk_level),
                    }}>
                      {port.risk_level}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span>Status:</span>
                    <span style={{ color: port.status === 'operational' ? '#10b981' : '#ef4444' }}>
                      {port.status}
                    </span>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}

          {/* Chokepoint Markers */}
          {CHOKEPOINTS.map((cp, i) => (
            <Marker
              key={i}
              position={[cp.lat, cp.lon]}
              icon={createChokepointIcon()}
            >
              <Popup>
                <div style={{ minWidth: 180 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, color: '#ef4444' }}>
                    ⚠ {cp.name}
                  </div>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    {cp.region}
                  </div>
                  <div style={{ fontSize: 12, marginTop: 6, fontStyle: 'italic' }}>
                    Critical maritime chokepoint
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

          <MapLegend />
        </MapContainer>
      </div>

      {/* Port Cards Below Map */}
      <div className="card-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        {loading ? (
          <div className="loading-spinner">Loading ports...</div>
        ) : (
          ports.map(port => (
            <div key={port.id} className="stat-card" style={{ borderLeft: `3px solid ${riskColor(port.risk_level)}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                    {port.name}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{port.country}</div>
                </div>
                <span className={`badge badge-${port.risk_level}`}>
                  {port.risk_level}
                </span>
              </div>
              <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                <span style={{ color: 'var(--text-muted)' }}>Risk: {port.risk_score}</span>
                <span style={{ color: port.status === 'operational' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                  ● {port.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}