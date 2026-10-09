with open('s:/QK/QUANTUM-KAVACHA-main/QUANTUM-KAVACHA-main/frontend/src/components/TransactionsWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write("""import React, { useState, useEffect } from 'react';
import { Search, Filter, AlertTriangle, Shield, CheckCircle, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

export function TransactionsWorkspace({ fastApiBase, onSelectTransaction }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch(`${fastApiBase}/api/transactions?limit=100`)
      .then(r => {
        if (!r.ok) throw new Error("Failed to fetch transactions");
        return r.json();
      })
      .then(data => {
        if (Array.isArray(data)) setTransactions(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, [fastApiBase]);

  const filtered = transactions.filter(t => 
    !search || 
    t.txn_id?.toLowerCase().includes(search.toLowerCase()) || 
    t.user_id?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="glass-panel" style={{ minHeight: '600px' }}>
      <div className="panel-header" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
        <h2><Search size={18} style={{ color: "var(--brand-primary)" }} /> Transaction Explorer</h2>
      </div>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <input 
          type="text" 
          placeholder="Search by Transaction ID or User ID..." 
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ 
            flex: 1, 
            padding: '0.5rem 1rem', 
            borderRadius: 'var(--radius-md)', 
            border: '1px solid var(--border-medium)', 
            background: 'var(--bg-surface-elevated)',
            color: 'var(--text-primary)'
          }} 
        />
        <button className="btn btn-secondary"><Filter size={14}/> Filter</button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>Loading transactions...</div>
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-critical)' }}>Error: {error}</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No transactions found.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-medium)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '0.75rem' }}>Transaction ID</th>
                <th style={{ padding: '0.75rem' }}>User ID</th>
                <th style={{ padding: '0.75rem' }}>Amount</th>
                <th style={{ padding: '0.75rem' }}>Risk Score</th>
                <th style={{ padding: '0.75rem' }}>Decision</th>
                <th style={{ padding: '0.75rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '0.75rem', fontFamily: 'JetBrains Mono' }}>{t.txn_id}</td>
                  <td style={{ padding: '0.75rem' }}>{t.user_id}</td>
                  <td style={{ padding: '0.75rem', fontFamily: 'JetBrains Mono' }}>
                    {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(t.amount || 0)}
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ 
                      color: t.risk_score >= 70 ? 'var(--color-high-risk)' : (t.risk_score >= 35 ? 'var(--color-caution)' : 'var(--color-safe)'),
                      fontWeight: 'bold',
                      fontFamily: 'JetBrains Mono'
                    }}>
                      {t.risk_score?.toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span className={`decision-pill ${t.decision?.toLowerCase()}`}>{t.decision}</span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <button className="btn btn-secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }} onClick={() => onSelectTransaction(t.txn_id)}>
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
""")
