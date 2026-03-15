import { useState, useEffect } from 'react';
import { RefreshCw, AlertTriangle, Shield, Activity, Radio } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE = 'http://localhost:8000/api/v1';

interface FeedItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  category: string;
  credibility: string;
  risk_score: number;
  published: string;
  keywords: string[];
}

interface Analysis {
  risk_level: string;
  risk_score: number;
  summary: string;
  recommendations: string[];
  chokepoints: Array<{
    name: string;
    status: string;
    risk_score: number;
    alternatives: Array<{ route: string; extra_days: number; extra_cost_pct: number }>;
  }>;
  provider: string;
  event_type: string;
}

interface DashboardStats {
  global_risk_index: number;
  active_disruptions: number;
  monitored_sources: number;
  supply_chain_health: number;
}

interface TrendPoint {
  date: string;
  score: number;
  level: string;
}

export default function Dashboard() {
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  const categories = ['all', 'maritime', 'conflict', 'weather', 'sanctions', 'news', 'humanitarian', 'labor'];

  useEffect(() => {
    fetchData();
    fetchAnalysis();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [feedRes, statsRes, trendRes] = await Promise.all([
        fetch(`${API_BASE}/intelligence/feed?limit=50`),
        fetch(`${API_BASE}/risk/dashboard`),
        fetch(`${API_BASE}/risk/trend`),
      ]);
      const feedData = await feedRes.json();
      const statsData = await statsRes.json();
      const trendData = await trendRes.json();

      setFeed(feedData.items || []);
      setStats(statsData);
      setTrend(trendData.trend || []);
    } catch (e) {
      console.error('Fetch error:', e);
    }
    setLoading(false);
  }

  async function fetchAnalysis() {
    setAnalysisLoading(true);
    try {
      const res = await fetch(`${API_BASE}/intelligence/analyze?entity=global&use_llm=true`);
      const data = await res.json();
      setAnalysis(data);
    } catch (e) {
      console.error('Analysis error:', e);
    }
    setAnalysisLoading(false);
  }

  async function handleRefresh() {
    setRefreshing(true);
    await fetchData();
    await fetchAnalysis();
    setRefreshing(false);
  }

  const filteredFeed = activeCategory === 'all'
    ? feed
    : feed.filter(item => item.category?.toLowerCase() === activeCategory);

  const riskBadgeClass = (level: string) => {
    const l = level?.toLowerCase();
    if (l === 'critical') return 'badge badge-critical';
    if (l === 'high') return 'badge badge-high';
    if (l === 'medium') return 'badge badge-medium';
    return 'badge badge-low';
  };

  return (
    <div>
      {/* Header */}
      <div className="section-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>ATLAS Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Real-time global supply chain risk intelligence</p>
        </div>
        <button className="btn btn-primary" onClick={handleRefresh} disabled={refreshing}>
          <RefreshCw size={14} className={refreshing ? 'spinning' : ''} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Stat Cards */}
      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-label"><Shield size={14} /> Global Risk Index</div>
          <div className="stat-value" style={{ color: 'var(--accent-red)' }}>
            {stats?.global_risk_index?.toFixed(1) || '—'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><AlertTriangle size={14} /> Active Disruptions</div>
          <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>
            {stats?.active_disruptions ?? '—'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><Radio size={14} /> OSINT Sources</div>
          <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>
            {stats?.monitored_sources ?? '—'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label"><Activity size={14} /> Supply Chain Health</div>
          <div className="stat-value" style={{ color: 'var(--accent-green)' }}>
            {stats?.supply_chain_health?.toFixed(1) || '—'}%
          </div>
        </div>
      </div>

      <div className="two-col-grid">
        {/* Left Column */}
        <div>
          {/* AI Analysis */}
          <div className="analysis-panel">
            <div className="section-header">
              <h2 className="section-title">🤖 AI Geopolitical Risk Assessment</h2>
              {analysis && <span className={riskBadgeClass(analysis.risk_level)}>{analysis.risk_level}</span>}
            </div>
            {analysisLoading ? (
              <div className="loading-spinner">Analyzing intelligence...</div>
            ) : analysis ? (
              <>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 16 }}>
                  {analysis.summary}
                </p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>
                  Provider: {analysis.provider} | Event Type: {analysis.event_type}
                </p>
                {analysis.recommendations?.length > 0 && (
                  <>
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Recommendations</h3>
                    <ul className="recommendations-list">
                      {analysis.recommendations.map((rec, i) => (
                        <li key={i}>→ {rec}</li>
                      ))}
                    </ul>
                  </>
                )}
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No analysis available</p>
            )}
          </div>

          {/* Chokepoint Status */}
          {analysis?.chokepoints && analysis.chokepoints.length > 0 && (
            <div className="card" style={{ marginBottom: 24 }}>
              <h2 className="section-title" style={{ marginBottom: 16 }}>🚢 Chokepoint Status</h2>
              <table className="chokepoint-table">
                <thead>
                  <tr>
                    <th>Chokepoint</th>
                    <th>Status</th>
                    <th>Risk</th>
                    <th>Alternative</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.chokepoints.map((cp, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 500 }}>{cp.name}</td>
                      <td>
                        <span className={`badge ${cp.status === 'elevated' ? 'badge-high' : 'badge-low'}`}>
                          {cp.status}
                        </span>
                      </td>
                      <td>{cp.risk_score?.toFixed(0)}</td>
                      <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {cp.alternatives?.[0]?.route || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Risk Trend Chart */}
          {trend.length > 0 && (
            <div className="card" style={{ marginBottom: 24 }}>
              <h2 className="section-title" style={{ marginBottom: 16 }}>📈 Risk Severity Trend</h2>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8 }}
                    labelStyle={{ color: 'var(--text-primary)' }}
                  />
                  <Line type="monotone" dataKey="score" stroke="var(--accent-blue)" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Right Column — Alerts */}
        <div>
          <div className="card">
            <h2 className="section-title" style={{ marginBottom: 16 }}>🚨 Recent Alerts</h2>
            {feed.filter(i => i.risk_score >= 60).slice(0, 8).map((item) => (
              <div key={item.id} className="feed-item">
                <div className="feed-item-title">{item.title}</div>
                <div className="feed-item-meta">
                  <span>{item.source}</span>
                  <span className={`badge ${item.risk_score >= 80 ? 'badge-critical' : 'badge-high'}`}>
                    {item.risk_score.toFixed(0)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* OSINT Feed */}
      <div className="card">
        <div className="section-header">
          <h2 className="section-title">📡 OSINT Intelligence Feed</h2>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{filteredFeed.length} items</span>
        </div>

        <div className="feed-tabs">
          {categories.map(cat => (
            <button
              key={cat}
              className={`feed-tab ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading-spinner">Loading intelligence feed...</div>
        ) : (
          filteredFeed.slice(0, 20).map((item) => (
            <div key={item.id} className="feed-item">
              <div className="feed-item-title">{item.title}</div>
              <div className="feed-item-summary">{item.summary?.substring(0, 200)}</div>
              <div className="feed-item-meta">
                <span>{item.source}</span>
                <span>{item.category}</span>
                <span className={riskBadgeClass(item.risk_score >= 70 ? 'high' : item.risk_score >= 40 ? 'medium' : 'low')}>
                  Risk: {item.risk_score?.toFixed(0)}
                </span>
                <span>{item.credibility}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}