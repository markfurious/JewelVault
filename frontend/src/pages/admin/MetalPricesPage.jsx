import React, { useState, useEffect } from 'react';

const API_BASE = '/api/v1';

function MetalPricesPage() {
  const [metalPrices, setMetalPrices] = useState(null);
  const [priceHistory, setPriceHistory] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [updateResult, setUpdateResult] = useState(null);
  const [selectedMetal, setSelectedMetal] = useState('gold');
  const [threshold, setThreshold] = useState(5.0);

  useEffect(() => {
    loadPrices();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const loadPrices = async () => {
    try {
      const response = await fetch(`${API_BASE}/metal-prices/latest`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setMetalPrices(data);
      }
    } catch (err) {
      setError('Failed to load prices: ' + err.message);
    }
  };

  const handleUpdatePrices = async () => {
    setLoading(true);
    setError(null);
    setUpdateResult(null);

    try {
      const response = await fetch(`${API_BASE}/metal-prices/update`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const result = await response.json();
        setUpdateResult(result);
        loadPrices();
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to update prices');
      }
    } catch (err) {
      setError('Failed to update prices: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateJewelryPrices = async () => {
    setLoading(true);
    setError(null);
    setUpdateResult(null);

    try {
      const response = await fetch(
        `${API_BASE}/metal-prices/update-jewelry-prices?metal_type=${selectedMetal}&threshold=${threshold}`,
        {
          method: 'POST',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const result = await response.json();
        setUpdateResult(result);
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to update jewelry prices');
      }
    } catch (err) {
      setError('Failed to update jewelry prices: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPriceHistory = async (metal) => {
    try {
      const response = await fetch(
        `${API_BASE}/metal-prices/history/${metal}?days=30`,
        { headers: getAuthHeaders() }
      );
      if (response.ok) {
        const data = await response.json();
        setPriceHistory(prev => ({ ...prev, [metal]: data.history }));
      }
    } catch (err) {
      setError('Failed to load history: ' + err.message);
    }
  };

  const formatPrice = (price) => {
    if (!price) return '-';
    return `$${parseFloat(price).toFixed(2)}`;
  };

  const formatPercent = (percent) => {
    if (percent === null || percent === undefined) return '-';
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  const getChangeColor = (change) => {
    if (change === null || change === undefined) return '#6b7280';
    return change >= 0 ? '#16a34a' : '#dc2626';
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Metal Price Management</h1>
      <p style={styles.description}>
        Track precious metal prices and automatically update jewelry prices based on market changes.
      </p>

      {/* Current Prices */}
      <div style={styles.card}>
        <h2 style={styles.subheading}>Current Metal Prices</h2>
        <div style={styles.pricesGrid}>
          {['gold', 'silver', 'platinum'].map(metal => (
            <div
              key={metal}
              style={{
                ...styles.priceCard,
                borderLeft: `4px solid ${metal === 'gold' ? '#fbbf24' : metal === 'silver' ? '#94a3b8' : '#e5e4e2'}`
              }}
            >
              <div style={styles.priceHeader}>
                <span style={styles.metalName}>{metal.charAt(0).toUpperCase() + metal.slice(1)}</span>
                <span style={styles.priceValue}>
                  {metalPrices && metalPrices[metal] ? formatPrice(metalPrices[metal].price_per_gram) : '-'}
                </span>
              </div>
              <div style={styles.priceUnit}>per gram (USD)</div>
            </div>
          ))}
        </div>

        <button
          onClick={handleUpdatePrices}
          disabled={loading}
          style={loading ? styles.buttonDisabled : styles.button}
        >
          {loading ? 'Updating...' : 'Fetch Latest Prices'}
        </button>
      </div>

      {/* Update Result */}
      {updateResult && (
        <div style={styles.resultCard}>
          <h3 style={styles.resultTitle}>Last Update Result</h3>
          <pre style={styles.resultPre}>{JSON.stringify(updateResult, null, 2)}</pre>
        </div>
      )}

      {/* Update Jewelry Prices */}
      <div style={styles.card}>
        <h2 style={styles.subheading}>Update Jewelry Prices</h2>
        <p style={styles.description}>
          Automatically adjust jewelry prices based on metal price changes.
          Only triggers if change exceeds the threshold.
        </p>

        <div style={styles.formRow}>
          <label style={styles.label}>
            Metal Type:
            <select
              value={selectedMetal}
              onChange={(e) => setSelectedMetal(e.target.value)}
              style={styles.select}
            >
              <option value="gold">Gold</option>
              <option value="silver">Silver</option>
              <option value="platinum">Platinum</option>
            </select>
          </label>

          <label style={styles.label}>
            Threshold (%):
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              style={styles.input}
              step="0.1"
              min="0"
            />
          </label>
        </div>

        <button
          onClick={handleUpdateJewelryPrices}
          disabled={loading}
          style={loading ? styles.buttonDisabled : styles.button}
        >
          {loading ? 'Updating...' : 'Update Jewelry Prices'}
        </button>
      </div>

      {/* Price History */}
      <div style={styles.card}>
        <h2 style={styles.subheading}>Price History</h2>
        <div style={styles.historyTabs}>
          {['gold', 'silver', 'platinum'].map(metal => (
            <button
              key={metal}
              onClick={() => loadPriceHistory(metal)}
              style={metal === selectedMetal ? styles.activeTab : styles.tab}
            >
              {metal.charAt(0).toUpperCase() + metal.slice(1)}
            </button>
          ))}
        </div>

        {priceHistory[selectedMetal] && (
          <div style={styles.historyList}>
            {priceHistory[selectedMetal].slice(0, 10).map((item, index) => (
              <div key={index} style={styles.historyItem}>
                <span style={styles.historyDate}>
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
                <span style={styles.historyPrice}>
                  {formatPrice(item.price_per_gram)}
                </span>
                <span style={styles.historySource}>
                  {item.source}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Error */}
      {error && <div style={styles.error}>{error}</div>}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1000px',
    margin: '0 auto',
    padding: '24px',
  },
  heading: {
    fontSize: '28px',
    fontWeight: '700',
    marginBottom: '8px',
    color: '#1a1a2e',
  },
  description: {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '24px',
  },
  card: {
    background: '#fff',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  subheading: {
    fontSize: '18px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#1a1a2e',
  },
  pricesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    marginBottom: '20px',
  },
  priceCard: {
    background: '#f9fafb',
    borderRadius: '8px',
    padding: '16px',
  },
  priceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  metalName: {
    fontSize: '16px',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  priceValue: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#1a1a2e',
  },
  priceUnit: {
    fontSize: '12px',
    color: '#6b7280',
  },
  button: {
    background: '#4f46e5',
    color: '#fff',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  buttonDisabled: {
    background: '#9ca3af',
    color: '#fff',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'not-allowed',
  },
  resultCard: {
    background: '#f0fdf4',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '20px',
    border: '1px solid #16a34a',
  },
  resultTitle: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#16a34a',
    marginBottom: '8px',
  },
  resultPre: {
    background: 'transparent',
    padding: 0,
    margin: 0,
    fontSize: '12px',
    color: '#374151',
    whiteSpace: 'pre-wrap',
  },
  formRow: {
    display: 'flex',
    gap: '24px',
    marginBottom: '16px',
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    fontSize: '14px',
    fontWeight: '500',
  },
  select: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    fontSize: '14px',
    minWidth: '200px',
  },
  input: {
    padding: '8px 12px',
    borderRadius: '6px',
    border: '1px solid #d1d5db',
    fontSize: '14px',
    width: '150px',
  },
  historyTabs: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
  },
  tab: {
    padding: '8px 16px',
    background: '#f3f4f6',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  },
  activeTab: {
    padding: '8px 16px',
    background: '#4f46e5',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  },
  historyList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  historyItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px',
    background: '#f9fafb',
    borderRadius: '6px',
    fontSize: '14px',
  },
  historyDate: {
    color: '#6b7280',
  },
  historyPrice: {
    fontWeight: '600',
    color: '#1a1a2e',
  },
  historySource: {
    color: '#9ca3af',
    fontSize: '12px',
  },
  error: {
    background: '#fef2f2',
    color: '#dc2626',
    padding: '12px',
    borderRadius: '6px',
    fontSize: '14px',
  },
};

export default MetalPricesPage;
