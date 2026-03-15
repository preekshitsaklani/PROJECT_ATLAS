import { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

interface RiskScore {
  entity_id: string;
  name: string;
  country: string;
  composite_score: number;
  level: string;
  components: {
    time_series: number;
    nlp_sentiment: number;
    graph_centrality: number;
    weather_impact: number;
    financial_stress: number;
  };
}

export default function RiskIntelligence() {
  const [scores, setScores] = useState<RiskScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchScores();
  }, []);

  async function fetchScores() {
    try {
      const res = await fetch(`${API_BASE}/risk/scores`);
      const data = await res.json();
      setScores(data.scores || []);
    } catch (e) {
      console.error('Scores fetch error:', e);
    }
    setLoading(false);
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API_BASE}/intelligence/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 20 }),
      });
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (e) {
      console.error('Search error:', e);
    }
    setSearching(false);
  }

  const riskColor = (level: string) => {
    if (level === 'critical') return 'var(--accent-red)';
    if (level === 'high') return 'var(--accent-amber)';
    if (level === 'medium') return 'var(--accent-blue)';
    return 'var(--accent-green)';
  };

  return (
    <div>
      <div className="section-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>Risk Intelligence</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Deep-dive risk analysis and entity-specific breakdowns</p>
        </div>
      </div>

      {/* Semantic Search */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h2 className="section-title" style={{ marginBottom: 12 }}>🔍 Intelligence Search (RAG)</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            placeholder="Search intelligence... (e.g., 'Red Sea shipping attacks')"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            style={{
              flex: 1,
              padding: '10px 16px',
              borderRadius: 8,
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              fontSize: 14,
            }}
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={searching}>
            <Search size={14} />
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div style={{ marginTop: 16 }}>
            {searchResults.map((result, i) => (
              <div key={i} className="feed-item">
                <div className="feed-item-title">{result.title}</div>
                <div className="feed-item-summary">{result.summary?.substring(0, 200)}</div>
                <div className="feed-item-meta">
                  <span>{result.source}</span>
                  <span>Score: {result._score?.toFixed(3)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Entity Risk Breakdown */}
      <div className="card">
        <h2 className="section-title" style={{ marginBottom: 16 }}>📊 Entity Risk Breakdown</h2>
        {loading ? (
          <div className="loading-spinner">Loading risk scores...</div>
        ) : (
          <table className="chokepoint-table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Country</th>
                <th>Risk Score</th>
                <th>Level</th>
                <th>NLP</th>
                <th>Weather</th>
                <th>Financial</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((score) => (
                <tr key={score.entity_id}>
                  <td style={{ fontWeight: 500 }}>{score.name}</td>
                  <td>{score.country}</td>
                  <td style={{ color: riskColor(score.level), fontWeight: 700 }}>
                    {score.composite_score}
                  </td>
                  <td><span className={`badge badge-${score.level}`}>{score.level}</span></td>
                  <td>{score.components?.nlp_sentiment}</td>
                  <td>{score.components?.weather_impact}</td>
                  <td>{score.components?.financial_stress}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}