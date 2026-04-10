import React, { useState, useRef, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { inventoryApi } from '../services/api';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

export default function InventoryPage() {
  const gridRef = useRef(null);
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [adjustForm, setAdjustForm] = useState({ productId: null, status: 'AVAILABLE', notes: '' });
  const [searchValue, setSearchValue] = useState('');

  const [columnDefs] = useState([
    {
      field: 'product_sku',
      headerName: 'SKU',
      width: 100,
      filter: true,
      pinned: 'left',
      cellStyle: { fontWeight: '600' },
    },
    {
      field: 'product_name',
      headerName: 'Product',
      width: 250,
      filter: true,
    },
    {
      field: 'status',
      headerName: 'Item Status',
      width: 110,
      filter: true,
      cellStyle: { textAlign: 'center', fontWeight: '600' },
      cellRenderer: (params) => {
        const status = params.value || 'AVAILABLE';
        let className = 'badge ';
        if (status === 'AVAILABLE') className += 'badge-success';
        else if (status === 'SOLD') className += 'badge-danger';
        else if (status === 'RESERVED') className += 'badge-warning';
        return <span className={className}>{status}</span>;
      },
    },
    {
      field: 'location',
      headerName: 'Location',
      width: 120,
      filter: true,
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
    loadInventory();
  }, []);

  async function loadInventory() {
    try {
      setLoading(true);
      const response = await inventoryApi.list({ limit: 100 });
      setRowData(response.items || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const handleAdjust = async (e) => {
    e.preventDefault();
    try {
      await inventoryApi.adjust(adjustForm.productId, {
        status: adjustForm.status,
        transaction_type: 'ADJUSTMENT',
        notes: adjustForm.notes,
      });
      setAdjustForm({ productId: null, status: 'AVAILABLE', notes: '' });
      loadInventory();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleQuickFilter = () => {
    if (gridRef.current) {
      gridRef.current.api.setQuickFilter(searchValue);
    }
  };

  useEffect(() => {
    handleQuickFilter();
  }, [searchValue]);

  const getRowId = (params) => {
    return params.data.id;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Inventory Management</h1>
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
          <button className="btn btn-primary" onClick={loadInventory}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {adjustForm.productId && (
        <div className="card mb-16">
          <div className="flex flex-between mb-16">
            <h3 style={{ fontSize: '14px', fontWeight: '600' }}>
              Update Item Status - {adjustForm.productId}
            </h3>
            <button
              type="button"
              className="btn btn-sm"
              onClick={() => setAdjustForm({ productId: null, status: '', notes: '' })}
            >
              × Close
            </button>
          </div>
          <form onSubmit={handleAdjust}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  className="form-input"
                  value={adjustForm.status || 'AVAILABLE'}
                  onChange={(e) => setAdjustForm({ ...adjustForm, status: e.target.value })}
                >
                  <option value="AVAILABLE">AVAILABLE</option>
                  <option value="SOLD">SOLD</option>
                  <option value="RESERVED">RESERVED</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <input
                  type="text"
                  className="form-input"
                  value={adjustForm.notes}
                  onChange={(e) => setAdjustForm({ ...adjustForm, notes: e.target.value })}
                  placeholder="Reason for status change"
                />
              </div>
            </div>
            <div className="flex gap-8">
              <button type="submit" className="btn btn-success">Update Status</button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setAdjustForm({ productId: null, status: '', notes: '' })}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="ag-grid-container">
        <div
          className="ag-theme-alpine"
          style={{ width: '100%', height: 'calc(100vh - 220px)', minHeight: '300px' }}
        >
          {loading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              Loading inventory...
            </div>
          ) : (
            <AgGridReact
              ref={gridRef}
              rowData={rowData}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              getRowId={getRowId}
              pagination={true}
              paginationPageSize={100}
              paginationPageSizeSelector={[50, 100, 200, 500]}
              rowSelection={'multiple'}
              animateRows={false}
              suppressCellFocus={true}
              theme="legacy"
              onRowDoubleClick={(params) => {
                setAdjustForm({ ...adjustForm, productId: params.data.product_id, status: params.data.status || 'AVAILABLE' });
              }}
            />
          )}
        </div>
      </div>

      <div style={{ marginTop: '12px', fontSize: '12px', color: '#718096' }}>
        💡 Tip: Double-click on a row to quickly update item status
      </div>
    </div>
  );
}
