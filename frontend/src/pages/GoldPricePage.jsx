import React, { useState, useEffect } from 'react';

const API_BASE = '/api/v1';

async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = localStorage.getItem('access_token');

  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
      }
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

export default function GoldPricePage() {
  const [goldData, setGoldData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPrice, setCurrentPrice] = useState(null);

  const fetchGoldPrice = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchApi('/gold/price');

      if (data && data.current_price) {
        setCurrentPrice(data.current_price);
        setGoldData(prev => {
          const newEntry = {
            date: new Date().toISOString().split('T')[0],
            price: data.current_price,
          };
          const updated = [newEntry, ...prev].slice(0, 30);
          return updated;
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch gold price');
    } finally {
      setLoading(false);
    }
  };

  const handleGetData = () => {
    fetchGoldPrice();
  };

  const clearData = () => {
    setGoldData([]);
    setCurrentPrice(null);
    setError(null);
  };

  // Simple SVG chart
  const Chart = ({ data }) => {
    if (!data || data.length === 0) return null;

    const width = 800;
    const height = 400;
    const padding = 60;

    const prices = data.map(d => d.price);
    const minPrice = Math.min(...prices) * 0.99;
    const maxPrice = Math.max(...prices) * 1.01;
    const priceRange = maxPrice - minPrice;

    const xScale = (index) => padding + (index / (data.length - 1 || 1)) * (width - 2 * padding);
    const yScale = (price) => height - padding - ((price - minPrice) / priceRange) * (height - 2 * padding);

    const points = data.map((d, i) => `${xScale(i)},${yScale(d.price)}`).join(' ');
    const areaPoints = `${xScale(0)},${height - padding} ${points} ${xScale(data.length - 1)},${height - padding}`;

    const yTicks = 5;
    const yLabels = Array.from({ length: yTicks }, (_, i) => {
      const value = minPrice + (priceRange * i) / (yTicks - 1);
      return { value, y: yScale(value) };
    });

    const xLabels = data.filter((_, i) => i % Math.ceil(data.length / 5) === 0).map((d, i, arr) => ({
      date: d.date,
      x: xScale(i * Math.ceil(data.length / 5)),
    }));

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ background: '#fafafa', borderRadius: '8px' }}>
        {/* Grid lines */}
        {yLabels.map((tick, i) => (
          <line
            key={i}
            x1={padding}
            y1={tick.y}
            x2={width - padding}
            y2={tick.y}
            stroke="#e5e7eb"
            strokeDasharray="4,4"
          />
        ))}

        {/* Area fill */}
        <polygon points={areaPoints} fill="rgba(50, 54, 58, 0.1)" />

        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke="#32363a"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {data.map((d, i) => (
          <circle
            key={i}
            cx={xScale(i)}
            cy={yScale(d.price)}
            r="4"
            fill="#32363a"
            stroke="#fff"
            strokeWidth="2"
          >
            <title>{`${d.date}: $${d.price.toFixed(2)}`}</title>
          </circle>
        ))}

        {/* Y-axis labels */}
        {yLabels.map((tick, i) => (
          <text
            key={i}
            x={padding - 10}
            y={tick.y + 4}
            textAnchor="end"
            fontSize="11"
            fill="#666"
          >
            ${tick.value.toFixed(0)}
          </text>
        ))}

        {/* X-axis labels */}
        {xLabels.map((label, i) => (
          <text
            key={i}
            x={label.x}
            y={height - padding + 20}
            textAnchor="middle"
            fontSize="10"
            fill="#666"
          >
            {label.date}
          </text>
        ))}

        {/* Axis lines */}
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#32363a" strokeWidth="2" />
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#32363a" strokeWidth="2" />

        {/* Title */}
        <text x={width / 2} y={25} textAnchor="middle" fontSize="14" fontWeight="600" fill="#32363a">
          Gold Price History (per oz)
        </text>
      </svg>
    );
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Gold Price Tracker</h1>
        <div className="action-bar">
          <button
            className="btn btn-primary"
            onClick={handleGetData}
            disabled={loading}
          >
            {loading ? 'Fetching...' : 'Get Data'}
          </button>
          <button
            className="btn"
            onClick={clearData}
            disabled={goldData.length === 0}
          >
            Clear Data
          </button>
        </div>
      </div>

      <div style={{ padding: '24px', background: '#fff', borderRadius: '8px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: '600' }}>Current Gold Price</h2>
            <p style={{ margin: 0, color: '#666', fontSize: '13px' }}>Price per troy ounce (USD)</p>
          </div>
          {currentPrice && (
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#32363a' }}>
              ${currentPrice.toFixed(2)}
            </div>
          )}
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginTop: '16px' }}>
            {error}
          </div>
        )}

        {goldData.length > 0 ? (
          <div style={{ marginTop: '24px' }}>
            <Chart data={goldData} />
            <div style={{ marginTop: '16px', fontSize: '12px', color: '#666' }}>
              Showing last {goldData.length} data point(s)
            </div>
          </div>
        ) : (
          <div style={{
            marginTop: '40px',
            padding: '40px',
            textAlign: 'center',
            background: '#fafafa',
            borderRadius: '8px',
            border: '1px dashed #ccc'
          }}>
            <p style={{ color: '#666', margin: 0 }}>
              Click "Get Data" to fetch the current gold price
            </p>
          </div>
        )}
      </div>

      {goldData.length > 0 && (
        <div style={{ background: '#fff', borderRadius: '8px', padding: '16px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>Price History</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #32363a' }}>
                <th style={{ padding: '8px', textAlign: 'left' }}>Date</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Price (USD/oz)</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Change</th>
              </tr>
            </thead>
            <tbody>
              {goldData.map((entry, i) => {
                const prevPrice = goldData[i + 1]?.price;
                const change = prevPrice ? entry.price - prevPrice : 0;
                const changePercent = prevPrice ? ((change / prevPrice) * 100) : 0;
                return (
                  <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '8px' }}>{entry.date}</td>
                    <td style={{ padding: '8px', textAlign: 'right', fontWeight: '600' }}>
                      ${entry.price.toFixed(2)}
                    </td>
                    <td style={{
                      padding: '8px',
                      textAlign: 'right',
                      color: change >= 0 ? '#276749' : '#c53030'
                    }}>
                      {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
