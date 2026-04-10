import React, { useState, useRef, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { analyticsApi } from '../services/api';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

export default function ReorderSuggestionsPage() {
  const gridRef = useRef(null);
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchValue, setSearchValue] = useState('');
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  const [columnDefs] = useState([
    {
      field: 'is_urgent',
      headerName: 'Priority',
      width: 90,
      filter: true,
      cellRenderer: (params) => {
        if (params.value) return <span className="badge badge-danger">URGENT</span>;
        if (params.data.is_fast_moving) return <span className="badge badge-info">Fast</span>;
        return <span className="badge badge-success">Normal</span>;
      },
    },
    {
      field: 'product_sku',
      headerName: 'SKU',
      width: 100,
      filter: true,
      cellStyle: { fontWeight: '600' },
    },
    {
      field: 'product_name',
      headerName: 'Product',
      width: 200,
      filter: true,
    },
    {
      field: 'current_stock',
      headerName: 'Current Stock',
      width: 100,
      filter: true,
      cellStyle: (params) => ({
        fontWeight: '600',
        color: params.data.current_stock < params.data.min_threshold ? '#c53030' : 'inherit',
      }),
    },
    {
      field: 'min_threshold',
      headerName: 'Min Threshold',
      width: 100,
      filter: true,
    },
    {
      field: 'sales_velocity',
      headerName: 'Daily Velocity',
      width: 110,
      filter: true,
      valueFormatter: (params) => `${params.value?.toFixed(2) || '0.00'} units/day`,
    },
    {
      field: 'estimated_days_until_stockout',
      headerName: 'Stockout In',
      width: 110,
      filter: true,
      valueFormatter: (params) => {
        if (!params.value) return 'N/A';
        if (params.value <= 7) return `${Math.round(params.value)} days (Critical)`;
        if (params.value <= 14) return `${Math.round(params.value)} days (Soon)`;
        return `${Math.round(params.value)} days`;
      },
    },
    {
      field: 'recommended_reorder_quantity',
      headerName: 'Reorder Qty',
      width: 100,
      filter: true,
      cellStyle: { fontWeight: '600', color: '#276749' },
    },
  ]);

  const defaultColDef = {
    sortable: true,
    resizable: true,
    filter: true,
    flex: 0,
    minWidth: 60,
  };

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [suggestionsData, summaryData] = await Promise.all([
        analyticsApi.getReorderSuggestions(),
        analyticsApi.getInventorySummary(),
      ]);
      console.log('Reorder suggestions:', suggestionsData);
      console.log('Inventory summary:', summaryData);
      setRowData(suggestionsData.items || []);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load reorder suggestions:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  const handleQuickFilter = () => {
    if (gridRef.current) {
      gridRef.current.api.setQuickFilter(searchValue);
    }
  };

  useEffect(() => {
    handleQuickFilter();
  }, [searchValue]);

  const getRowId = (params) => {
    return params.data.product_id;
  };

  const urgentCount = rowData.filter((s) => s.is_urgent).length;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Smart Reorder Suggestions</h1>
        <div className="action-bar">
          <div className="search-bar">
            <span>🔍</span>
            <input
              type="text"
              placeholder="Search..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={loadData}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {summary && (
        <div className="dashboard-grid" style={{ marginBottom: '16px' }}>
          <div className="dashboard-card" style={{ borderTop: '3px solid #4299e1' }}>
            <div className="dashboard-card-icon">📦</div>
            <div className="dashboard-card-title">Total Products</div>
            <div className="dashboard-card-value">{summary.total_products}</div>
          </div>
          <div className="dashboard-card" style={{ borderTop: '3px solid #f56565' }}>
            <div className="dashboard-card-icon">⚠️</div>
            <div className="dashboard-card-title">Low Stock</div>
            <div className="dashboard-card-value" style={{ color: '#f56565' }}>{summary.low_stock_count}</div>
          </div>
          <div className="dashboard-card" style={{ borderTop: '3px solid #c53030' }}>
            <div className="dashboard-card-icon">🚫</div>
            <div className="dashboard-card-title">Out of Stock</div>
            <div className="dashboard-card-value" style={{ color: '#c53030' }}>{summary.out_of_stock_count}</div>
          </div>
          <div className="dashboard-card" style={{ borderTop: '3px solid #ed8936' }}>
            <div className="dashboard-card-icon">📈</div>
            <div className="dashboard-card-title">Overstock</div>
            <div className="dashboard-card-value" style={{ color: '#ed8936' }}>{summary.overstock_count}</div>
          </div>
          <div className="dashboard-card" style={{ borderTop: '3px solid #48bb78' }}>
            <div className="dashboard-card-icon">💰</div>
            <div className="dashboard-card-title">Stock Value</div>
            <div className="dashboard-card-value" style={{ color: '#48bb78', fontSize: '18px' }}>
              ${summary.total_stock_value?.toFixed(0) || '0'}
            </div>
          </div>
        </div>
      )}

      <div className="ag-grid-container">
        <div
          className="ag-theme-alpine"
          style={{ width: '100%', height: 'calc(100vh - 280px)', minHeight: '300px' }}
        >
          {loading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              Loading reorder suggestions...
            </div>
          ) : rowData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">✅</div>
              <div className="empty-state-text">
                All products are adequately stocked based on current sales velocity.
              </div>
            </div>
          ) : (
            <AgGridReact
              ref={gridRef}
              rowData={rowData}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              getRowId={getRowId}
              pagination={true}
              paginationPageSize={50}
              paginationPageSizeSelector={[25, 50, 100, 200]}
              rowSelection={'multiple'}
              animateRows={false}
              suppressCellFocus={true}
              theme="legacy"
              getRowStyle={(params) => {
                if (params.data.is_urgent) {
                  return { background: 'rgba(245, 101, 101, 0.08)' };
                }
                return undefined;
              }}
            />
          )}
        </div>
      </div>

      {rowData.length > 0 && (
        <div style={{ marginTop: '12px', fontSize: '12px', color: '#718096' }}>
          Showing {rowData.length} suggestions ({urgentCount} urgent)
        </div>
      )}
    </div>
  );
}
