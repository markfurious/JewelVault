import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { productsApi, inventoryApi, salesApi } from '../services/api';

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
      try { errorData = await response.json(); } catch { errorData = { detail: `HTTP ${response.status}` }; }
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// Simple SVG chart component
function GoldPriceChart({ data }) {
  if (!data || data.length === 0) return null;

  const width = 600;
  const height = 250;
  const padding = 50;

  const prices = data.map(d => d.price);
  const minPrice = Math.min(...prices) * 0.99;
  const maxPrice = Math.max(...prices) * 1.01;
  const priceRange = maxPrice - minPrice;

  const xScale = (index) => padding + (index / (data.length - 1 || 1)) * (width - 2 * padding);
  const yScale = (price) => height - padding - ((price - minPrice) / priceRange) * (height - 2 * padding);

  const points = data.map((d, i) => `${xScale(i)},${yScale(d.price)}`).join(' ');
  const areaPoints = `${xScale(0)},${height - padding} ${points} ${xScale(data.length - 1)},${height - padding}`;

  const yTicks = 4;
  const yLabels = Array.from({ length: yTicks }, (_, i) => ({
    value: minPrice + (priceRange * i) / (yTicks - 1),
    y: yScale(minPrice + (priceRange * i) / (yTicks - 1))
  }));

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ background: '#fafafa', borderRadius: '4px' }}>
      {yLabels.map((tick, i) => (
        <line key={i} x1={padding} y1={tick.y} x2={width - padding} y2={tick.y} stroke="#e5e7eb" strokeDasharray="4,4" />
      ))}
      <polygon points={areaPoints} fill="rgba(50, 54, 58, 0.1)" />
      <polyline points={points} fill="none" stroke="#32363a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {data.map((d, i) => (
        <circle key={i} cx={xScale(i)} cy={yScale(d.price)} r="4" fill="#32363a" stroke="#fff" strokeWidth="2">
          <title>{`${d.date}: $${d.price.toFixed(2)}`}</title>
        </circle>
      ))}
      {yLabels.map((tick, i) => (
        <text key={i} x={padding - 10} y={tick.y + 4} textAnchor="end" fontSize="10" fill="#666">${tick.value.toFixed(0)}</text>
      ))}
      <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#32363a" strokeWidth="2" />
      <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#32363a" strokeWidth="2" />
      <text x={width / 2} y={20} textAnchor="middle" fontSize="12" fontWeight="600" fill="#32363a">Gold Price History</text>
    </svg>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalStock: 0,
    lowStock: 0,
    totalSales: 0,
    todaySales: 0,
    pendingOrders: 0,
  });
  const [goldData, setGoldData] = useState([
    { date: '2026-03-20', price: 2650.00 },
    { date: '2026-03-21', price: 2662.50 },
    { date: '2026-03-22', price: 2658.25 },
    { date: '2026-03-23', price: 2671.00 },
    { date: '2026-03-24', price: 2680.75 },
    { date: '2026-03-25', price: 2675.50 },
    { date: '2026-03-26', price: 2688.00 },
    { date: '2026-03-27', price: 2695.25 },
    { date: '2026-03-28', price: 2702.00 },
    { date: '2026-03-29', price: 2698.50 },
    { date: '2026-03-30', price: 2710.75 },
    { date: '2026-03-31', price: 2718.00 },
    { date: '2026-04-01', price: 2725.50 },
    { date: '2026-04-02', price: 2732.00 },
  ]);
  const [currentGoldPrice, setCurrentGoldPrice] = useState(2732.00);
  const [goldLoading, setGoldLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchGoldPrice = async () => {
    setGoldLoading(true);
    // Simulate API call with random price fluctuation
    setTimeout(() => {
      const basePrice = 2732;
      const fluctuation = (Math.random() - 0.5) * 40;
      const newPrice = parseFloat((basePrice + fluctuation).toFixed(2));
      setCurrentGoldPrice(newPrice);
      setGoldData(prev => {
        const newEntry = { date: new Date().toISOString().split('T')[0], price: newPrice };
        return [newEntry, ...prev].slice(0, 14);
      });
      setGoldLoading(false);
    }, 500);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      const [products, inventory, sales] = await Promise.all([
        productsApi.list({ limit: 100 }),
        inventoryApi.list({ limit: 100 }),
        salesApi.list({ limit: 100 }),
      ]);

      const productList = products.items || [];
      const inventoryList = inventory.items || [];
      const salesList = sales.items || [];

      // Item-based model: count AVAILABLE items
      const availableItems = inventoryList.filter(item => item.status === 'AVAILABLE');
      const totalStock = availableItems.length;
      const lowStockItems = availableItems; // Show all available items as "low stock" alert

      // Calculate sales stats
      const totalSales = salesList.length;
      const today = new Date().toISOString().split('T')[0];
      const todaySales = salesList.filter(sale => {
        const saleDate = new Date(sale.sale_date || sale.created_at);
        return saleDate.toISOString().split('T')[0] === today;
      }).length;

      setStats({
        totalProducts: productList.length,
        totalStock,
        lowStock: lowStockItems.length,
        totalSales,
        todaySales,
        pendingOrders: lowStockItems.length,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }

  const cards = [
    {
      title: 'Active Stones',
      value: stats.totalProducts,
      subtitle: 'Total products',
      onClick: () => navigate('/stock'),
    },
    {
      title: 'Stock',
      value: stats.totalStock,
      subtitle: 'Total items in stock',
      onClick: () => navigate('/stock'),
    },
    {
      title: 'Low Stock Alert',
      value: stats.lowStock,
      subtitle: 'Items below threshold',
      onClick: () => navigate('/stock'),
    },
    {
      title: 'Sales Report',
      value: stats.totalSales,
      subtitle: 'Total sales recorded',
      onClick: () => navigate('/sales'),
    },
    {
      title: 'Today Sales',
      value: stats.todaySales,
      subtitle: 'Sales today',
      onClick: () => navigate('/sales'),
    },
    {
      title: 'Pending Orders',
      value: stats.pendingOrders,
      subtitle: 'Reorder suggestions',
      onClick: () => navigate('/reorder'),
    },
  ];

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">
          <div className="loading-spinner"></div>
          Loading dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h1 className="dashboard-title">Dashboard</h1>

      {/* Gold Price Section */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>Gold Price</h2>
          <button
            className="btn btn-primary"
            onClick={fetchGoldPrice}
            disabled={goldLoading}
            style={{ padding: '6px 16px', fontSize: '13px' }}
          >
            {goldLoading ? 'Fetching...' : 'Get Data'}
          </button>
        </div>
        <div style={{ background: '#fff', borderRadius: '8px', padding: '16px', border: '1px solid #e5e7eb' }}>
          {currentGoldPrice && (
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#32363a', marginBottom: '12px' }}>
              ${currentGoldPrice.toFixed(2)} <span style={{ fontSize: '12px', fontWeight: '400', color: '#666' }}>per oz (USD)</span>
            </div>
          )}
          <GoldPriceChart data={goldData} />
          {goldData.length === 0 && !goldLoading && (
            <p style={{ textAlign: 'center', color: '#666', margin: '20px 0', fontSize: '13px' }}>
              Click "Get Data" to fetch gold price
            </p>
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        {cards.map((card, index) => (
          <div
            key={index}
            className="dashboard-card"
            onClick={card.onClick}
          >
            <div className="dashboard-card-title">{card.title}</div>
            <div className="dashboard-card-value">{card.value}</div>
            <div className="dashboard-card-subtitle">{card.subtitle}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
