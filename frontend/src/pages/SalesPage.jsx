import React, { useState, useRef, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { salesApi } from '../services/api';

// Return request modal component
function ReturnRequestModal({ sale, onClose, onSuccess }) {
  const [productIds, setProductIds] = useState([]);
  const [reason, setReason] = useState('');
  const [refundAmount, setRefundAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (productIds.length === 0) {
      setError('Please select at least one product to return');
      return;
    }
    if (!reason.trim()) {
      setError('Please provide a return reason');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await salesApi.requestReturn(sale.id, {
        product_ids: productIds,
        reason: reason.trim(),
        refund_amount: refundAmount ? parseFloat(refundAmount) : null,
      });
      onSuccess();
    } catch (err) {
      setError(err.message || 'Failed to request return');
    } finally {
      setLoading(false);
    }
  };

  const toggleProduct = (productId) => {
    setProductIds(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <div className="modal-header">
          <h3 className="modal-title">Request Return - {sale.sale_number}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Products to Return</label>
            <div style={{ maxHeight: '150px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px' }}>
              {sale.items?.map(item => (
                <label key={item.product_id} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <input
                    type="checkbox"
                    checked={productIds.includes(item.product_id)}
                    onChange={() => toggleProduct(item.product_id)}
                  />
                  <span style={{ fontSize: '12px' }}>{item.product_sku} - {item.product_name} (${item.unit_price})</span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Return Reason *</label>
            <textarea
              className="form-input"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this return is requested"
              rows={3}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Refund Amount (optional)</label>
            <input
              type="number"
              className="form-input"
              value={refundAmount}
              onChange={(e) => setRefundAmount(e.target.value)}
              placeholder="Leave empty for automatic calculation"
              min="0"
              step="0.01"
            />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn" onClick={onClose} disabled={loading}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Submitting...' : 'Submit Return Request'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

export default function SalesPage() {
  const gridRef = useRef(null);
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchValue, setSearchValue] = useState('');
  const [selectedSale, setSelectedSale] = useState(null);
  const [showReturnModal, setShowReturnModal] = useState(false);

  const [columnDefs] = useState([
    {
      field: 'id',
      headerName: 'Sale ID',
      width: 220,
      filter: true,
      cellStyle: { fontFamily: 'monospace', fontSize: '11px' },
    },
    {
      field: 'customer_name',
      headerName: 'Customer',
      width: 150,
      filter: true,
    },
    {
      field: 'items',
      headerName: 'SKU(s)',
      width: 150,
      filter: true,
      cellStyle: { fontFamily: 'monospace', fontSize: '11px' },
      valueGetter: (params) => {
        if (!params.data.items || params.data.items.length === 0) return '';
        return params.data.items.map(item => item.product_sku).join(', ');
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      filter: true,
      cellRenderer: (params) => {
        const status = params.value;
        const statusUpper = (status || '').toUpperCase();
        return (
          <span style={{
            padding: '2px 8px',
            border: '1px solid #32363a',
            fontSize: '11px',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            background: statusUpper === 'COMPLETED' ? '#32363a' : '#fff',
            color: statusUpper === 'COMPLETED' ? '#fff' : '#32363a',
          }}>
            {statusUpper}
          </span>
        );
      },
    },
    {
      field: 'total_amount',
      headerName: 'Total Amount',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '$0.00',
      cellStyle: { textAlign: 'right', fontWeight: '600', color: '#276749' },
    },
    {
      field: 'tax_amount',
      headerName: 'Tax',
      width: 90,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '$0.00',
      cellStyle: { textAlign: 'right' },
    },
    {
      field: 'discount_amount',
      headerName: 'Discount',
      width: 90,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '$0.00',
      cellStyle: { textAlign: 'right', color: '#c53030' },
    },
    {
      field: 'item_count',
      headerName: 'Items',
      width: 70,
      filter: true,
      valueGetter: (params) => params.data.items?.length || 0,
      cellStyle: { textAlign: 'center' },
    },
    {
      field: 'payment_method',
      headerName: 'Payment',
      width: 100,
      filter: true,
    },
    {
      field: 'payment_status',
      headerName: 'Payment Status',
      width: 110,
      filter: true,
      cellRenderer: (params) => {
        const status = params.value;
        const statusUpper = (status || '').toUpperCase();
        return (
          <span style={{
            padding: '2px 8px',
            border: '1px solid #32363a',
            fontSize: '11px',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            background: statusUpper === 'PAID' ? '#32363a' : '#fff',
            color: statusUpper === 'PAID' ? '#fff' : '#32363a',
          }}>
            {statusUpper}
          </span>
        );
      },
    },
    {
      field: 'created_at',
      headerName: 'Created At',
      width: 160,
      filter: true,
      filterParams: {
        filterOptions: ['equals', 'notEqual', 'startsWith', 'endsWith'],
      },
      valueFormatter: (params) => {
        if (!params.value) return '-';
        return new Date(params.value).toLocaleString();
      },
    },
    {
      field: 'notes',
      headerName: 'Notes',
      width: 200,
      filter: true,
      cellStyle: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      cellRenderer: (params) => (
        <button
          className="btn btn-sm"
          onClick={() => handleRequestReturn(params.data)}
          disabled={params.data.status !== 'COMPLETED'}
          style={{ cursor: params.data.status !== 'COMPLETED' ? 'not-allowed' : 'pointer' }}
        >
          Request Return
        </button>
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
    loadSales();
  }, []);

  async function loadSales() {
    try {
      setLoading(true);
      const data = await salesApi.list({ limit: 100, status: 'COMPLETED' });
      setRowData(data.items || []);
    } catch (error) {
      console.error('Failed to load sales:', error);
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

  const handleRefresh = () => {
    loadSales();
  };

  const handleRequestReturn = (sale) => {
    if (sale.status !== 'COMPLETED') {
      alert('Returns can only be requested for completed sales');
      return;
    }
    setSelectedSale(sale);
    setShowReturnModal(true);
  };

  const handleReturnSuccess = () => {
    setShowReturnModal(false);
    setSelectedSale(null);
    loadSales();
    alert('Return request submitted successfully. Awaiting admin approval.');
  };

  const getRowId = (params) => {
    return params.data.id;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Sales Register</h1>
        <div className="action-bar">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search all columns..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={() => window.location.href = '/sales/create'}>
            New Sale
          </button>
          <button className="btn" onClick={handleRefresh}>
            Refresh
          </button>
        </div>
      </div>

      <div className="ag-grid-container">
        <div
          className="ag-theme-alpine"
          style={{ width: '100%', height: 'calc(100vh - 180px)' }}
        >
          {loading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              Loading sales data...
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
            />
          )}
        </div>
      </div>

      {showReturnModal && selectedSale && (
        <ReturnRequestModal
          sale={selectedSale}
          onClose={() => {
            setShowReturnModal(false);
            setSelectedSale(null);
          }}
          onSuccess={handleReturnSuccess}
        />
      )}
    </div>
  );
}
