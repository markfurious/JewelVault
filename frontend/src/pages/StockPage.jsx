import React, { useState, useCallback, useRef, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { stockApi } from '../services/api';
import BulkUploadModal from '../components/BulkUploadModal';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

export default function StockPage() {
  const gridRef = useRef(null);
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchValue, setSearchValue] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedCount, setSelectedCount] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);
  const [columnDefs] = useState([
    {
      field: 'sku',
      headerName: 'SKU',
      width: 100,
      pinned: 'left',
      filter: true,
      sort: 'asc',
      cellStyle: { fontWeight: '600', color: '#2d3748' },
    },
    {
      field: 'name',
      headerName: 'Product Name',
      width: 200,
      filter: true,
      cellStyle: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
      filter: true,
    },
    {
      field: 'sub_category',
      headerName: 'Sub Category',
      width: 120,
      filter: true,
    },
    {
      field: 'style_number',
      headerName: 'Style Number',
      width: 100,
      filter: true,
    },
    {
      field: 'st_carat',
      headerName: 'ST Carat',
      width: 90,
      filter: true,
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)} ct` : '-',
    },
    {
      field: 'product_weight',
      headerName: 'Product Wt (g)',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `${params.value.toFixed(2)} g` : '-',
    },
    {
      field: 'gold_purity',
      headerName: 'Gold Purity',
      width: 100,
      filter: true,
      cellStyle: { fontWeight: '500' },
    },
    {
      field: 'certified',
      headerName: 'Certified',
      width: 80,
      filter: true,
      cellRenderer: (params) => (
        <span style={{
          padding: '2px 8px',
          border: '1px solid #32363a',
          fontSize: '11px',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.3px',
          background: params.value ? '#32363a' : '#fff',
          color: params.value ? '#fff' : '#32363a',
        }}>
          {params.value ? 'Yes' : 'No'}
        </span>
      ),
    },
    {
      field: 'wholesale_price',
      headerName: 'Wholesale Price',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '-',
      cellStyle: { textAlign: 'right' },
    },
    {
      field: 'retail_price',
      headerName: 'Retail Price',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '-',
      cellStyle: { textAlign: 'right', fontWeight: '600', color: '#276749' },
    },
    {
      field: 'online_price',
      headerName: 'Online Price',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '-',
      cellStyle: { textAlign: 'right' },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      filter: true,
      cellStyle: { textAlign: 'center', fontWeight: '600' },
      cellRenderer: (params) => {
        const status = params.value || 'AVAILABLE';
        return (
          <span style={{
            padding: '2px 8px',
            border: '1px solid #32363a',
            fontSize: '11px',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            background: status === 'AVAILABLE' ? '#32363a' : '#fff',
            color: status === 'AVAILABLE' ? '#fff' : '#32363a',
          }}>
            {status}
          </span>
        );
      },
    },
    {
      field: 'is_active',
      headerName: 'Active',
      width: 70,
      filter: true,
      cellRenderer: (params) => params.value !== false ? (
        <span className="badge badge-success">Yes</span>
      ) : (
        <span className="badge badge-secondary">No</span>
      ),
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
    loadProducts();
  }, []);

  async function loadProducts() {
    try {
      setLoading(true);
      setError(null);
      const data = await stockApi.list({ limit: 100, status: 'AVAILABLE' });
      setRowData(data.items || []);
    } catch (err) {
      console.error('Failed to load stock data:', err);
      // Handle different error types
      let errorMsg = 'Failed to load stock data';
      if (typeof err === 'string') {
        errorMsg = err;
      } else if (err.message) {
        errorMsg = err.message;
      } else if (err.detail) {
        errorMsg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  const onGridReady = useCallback((params) => {
    gridRef.current = params;
  }, []);

  const handleQuickFilter = useCallback(() => {
    if (gridRef.current) {
      gridRef.current.api.setQuickFilter(searchValue);
    }
  }, [searchValue]);

  useEffect(() => {
    handleQuickFilter();
  }, [searchValue, handleQuickFilter]);

  const handleSelectAll = useCallback(() => {
    if (gridRef.current) {
      gridRef.current.api.selectAll();
    }
  }, []);

  const handleRefresh = useCallback(() => {
    loadProducts();
  }, []);

  const handleDownloadTemplate = useCallback(() => {
    const template = `SKU,Category,Sub Category,Style Number,ST Carat,Product wt,Gold Purity,Certified,Wholesale Price,Retail Price,Online Price
SI00001,Rings,Gold,RG-001,,5.5,18K,FALSE,800,1500,1400
SI00002,Necklaces,Diamond,NK-001,0.75,8.2,14K,TRUE,2000,3500,3300`;

    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'product_upload_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleBulkUploadSuccess = useCallback(() => {
    loadProducts();
    setShowUploadModal(false);
  }, []);

  const getRowId = useCallback((params) => {
    return params.data.id || params.data.sku;
  }, []);

  // Track selected rows
  const onSelectionChanged = useCallback(() => {
    if (gridRef.current) {
      const selected = gridRef.current.api.getSelectedRows();
      setSelectedCount(selected.length);
    }
  }, []);

  // Bulk action handler
  const handleBulkAction = useCallback(async (action) => {
    if (!gridRef.current) return;

    const selectedRows = gridRef.current.api.getSelectedRows();
    if (selectedRows.length === 0) {
      setError('Please select at least one row');
      return;
    }

    // Extract product IDs from selected rows
    const ids = selectedRows.map(row => row.id);

    // Confirm action
    const actionLabels = {
      mark_sold: 'mark as SOLD',
      mark_reserved: 'mark as RESERVED',
    };

    if (!window.confirm(`Are you sure you want to ${actionLabels[action] || action} ${selectedRows.length} selected items?`)) {
      return;
    }

    try {
      setActionLoading(true);
      setError(null);

      const result = await stockApi.bulkAction(action, ids, `Bulk action: ${action}`);

      // Show success and refresh
      alert(`Success! ${result.updated_count} items updated to ${action.replace('mark_', '').toUpperCase()}`);
      loadProducts();
    } catch (err) {
      console.error('Bulk action failed:', err);
      setError(err.message || 'Failed to execute bulk action');
    } finally {
      setActionLoading(false);
    }
  }, []);

  const handleClearSelection = useCallback(() => {
    if (gridRef.current) {
      gridRef.current.api.deselectAll();
      setSelectedCount(0);
    }
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Stock Management</h1>
        <div className="action-bar">
          <div className="search-bar">
            <span>🔍</span>
            <input
              type="text"
              placeholder="Search all columns..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
          </div>
          <button className="btn" onClick={handleSelectAll}>
            Select All
          </button>
          {selectedCount > 0 && (
            <>
              <button className="btn btn-danger" onClick={() => handleBulkAction('mark_sold')} disabled={actionLoading}>
                ❌ Mark Sold ({selectedCount})
              </button>
              <button className="btn btn-warning" onClick={() => handleBulkAction('mark_reserved')} disabled={actionLoading}>
                ⏸️ Mark Reserved ({selectedCount})
              </button>
              <button className="btn" onClick={handleClearSelection}>
                Clear
              </button>
            </>
          )}
          <button className="btn" onClick={() => setShowUploadModal(true)}>
            📤 Upload Excel
          </button>
          <button className="btn" onClick={handleDownloadTemplate}>
            📋 Template
          </button>
          <button className="btn btn-primary" onClick={handleRefresh}>
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="ag-grid-container">
        <div
          className="ag-theme-alpine"
          style={{ width: '100%', height: 'calc(100vh - 180px)', minHeight: '400px' }}
        >
          {loading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              Loading stock data...
            </div>
          ) : error ? (
            <div className="error-state">
              <div className="error-icon">⚠️</div>
              <h3>Failed to Load Stock Data</h3>
              <p className="error-message">{error}</p>
              <button className="btn btn-primary" onClick={handleRefresh}>
                Try Again
              </button>
            </div>
          ) : rowData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📦</div>
              <h3>No Stock Data</h3>
              <p className="empty-state-text">No products found in the system.</p>
              <button className="btn btn-primary" onClick={handleRefresh}>
                🔄 Refresh
              </button>
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
              tooltipMouseTrack={true}
              tooltipInteraction={true}
              theme="legacy"
              onGridReady={onGridReady}
              onSelectionChanged={onSelectionChanged}
            />
          )}
        </div>
      </div>

      {showUploadModal && (
        <BulkUploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleBulkUploadSuccess}
        />
      )}
    </div>
  );
}
