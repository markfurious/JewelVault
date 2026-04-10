import React, { useState, useEffect, useRef } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { salesApi } from '../services/api';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

// Return approval/rejection modal
function ReturnDecisionModal({ returnRequest, onClose, onSuccess }) {
  const [rejectionReason, setRejectionReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState(null); // 'approve' or 'reject'

  const handleSubmit = async () => {
    if (mode === 'reject' && !rejectionReason.trim()) {
      setError('Please provide a rejection reason');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (mode === 'approve') {
        await salesApi.approveReturn(returnRequest.id);
      } else {
        await salesApi.rejectReturn(returnRequest.id, { reason: rejectionReason.trim() });
      }

      onSuccess();
    } catch (err) {
      setError(err.message || 'Failed to process return');
    } finally {
      setLoading(false);
    }
  };

  const openApprove = () => {
    setMode('approve');
    setError(null);
  };

  const openReject = () => {
    setMode('reject');
    setError(null);
  };

  if (!mode) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
          <div className="modal-header">
            <h3 className="modal-title">Return Request - {returnRequest.id.slice(0, 8)}</h3>
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
          <div className="modal-body">
            <div style={{ marginBottom: '16px' }}>
              <strong>Sale ID:</strong> {returnRequest.sale_id.slice(0, 8)}...
            </div>
            <div style={{ marginBottom: '16px' }}>
              <strong>SKU(s):</strong>
              <p style={{ marginTop: '4px', fontFamily: 'monospace', fontSize: '12px' }}>
                {returnRequest.product_skus || 'N/A'}
              </p>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <strong>Refund Amount:</strong> ${parseFloat(returnRequest.refund_amount).toFixed(2)}
            </div>
            <div style={{ marginBottom: '16px' }}>
              <strong>Reason:</strong>
              <p style={{ marginTop: '4px', padding: '8px', background: '#f7fafc', borderRadius: '4px' }}>
                {returnRequest.reason}
              </p>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <strong>Requested By:</strong> {returnRequest.requested_by}
            </div>
            <div>
              <strong>Requested At:</strong> {new Date(returnRequest.requested_at).toLocaleString()}
            </div>
          </div>
          <div className="modal-footer" style={{ gap: '8px' }}>
            <button className="btn" onClick={onClose}>Cancel</button>
            <button className="btn btn-danger" onClick={openReject}>Reject</button>
            <button className="btn btn-success" onClick={openApprove}>Approve Refund</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <div className="modal-header">
          <h3 className="modal-title">
            {mode === 'approve' ? 'Approve Refund' : 'Reject Return'}
          </h3>
          <button className="modal-close" onClick={() => setMode(null)}>×</button>
        </div>
        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          {mode === 'reject' && (
            <div className="form-group">
              <label className="form-label">Rejection Reason *</label>
              <textarea
                className="form-input"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Explain why this return is rejected"
                rows={4}
                required
              />
            </div>
          )}

          {mode === 'approve' && (
            <div className="alert alert-success">
              Approving this return will:
              <ul style={{ margin: '8px 0 0 16px' }}>
                <li>Set items back to AVAILABLE status</li>
                <li>Mark the sale payment as REFUNDED</li>
                <li>Record the approval in the audit log</li>
              </ul>
            </div>
          )}
        </div>
        <div className="modal-footer" style={{ gap: '8px' }}>
          <button className="btn" onClick={() => setMode(null)} disabled={loading}>Back</button>
          {mode === 'reject' && (
            <button className="btn btn-danger" onClick={handleSubmit} disabled={loading}>
              {loading ? 'Rejecting...' : 'Confirm Rejection'}
            </button>
          )}
          {mode === 'approve' && (
            <button className="btn btn-success" onClick={handleSubmit} disabled={loading}>
              {loading ? 'Processing...' : 'Confirm Approval'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AdminReturnsPage() {
  const gridRef = useRef(null);
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [selectedReturn, setSelectedReturn] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const handleApprove = async (returnRequest) => {
    if (!window.confirm(`Approve return for SKU(s): ${returnRequest.product_skus || 'N/A'}?\n\nThis will restore the items to stock.`)) {
      return;
    }
    try {
      await salesApi.approveReturn(returnRequest.id);
      alert('Return approved - items restored to stock');
      loadReturns();
    } catch (err) {
      alert('Failed to approve return: ' + (err.message || 'Unknown error'));
    }
  };

  const handleReject = async (returnRequest) => {
    const reason = prompt('Enter rejection reason (required):');
    if (!reason || !reason.trim()) {
      alert('Rejection reason is required');
      return;
    }
    try {
      await salesApi.rejectReturn(returnRequest.id, { reason: reason.trim() });
      alert('Return rejected - items remain as sold');
      loadReturns();
    } catch (err) {
      alert('Failed to reject return: ' + (err.message || 'Unknown error'));
    }
  };

  const [columnDefs] = useState([
    {
      field: 'id',
      headerName: 'Return ID',
      width: 220,
      filter: true,
      cellStyle: { fontFamily: 'monospace', fontSize: '11px' },
    },
    {
      field: 'sale_id',
      headerName: 'Sale ID',
      width: 220,
      filter: true,
      cellStyle: { fontFamily: 'monospace', fontSize: '11px' },
    },
    {
      field: 'product_skus',
      headerName: 'SKU(s)',
      width: 150,
      filter: true,
      cellStyle: { fontFamily: 'monospace', fontSize: '11px' },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 110,
      filter: true,
      cellRenderer: (params) => {
        const status = params.value;
        return (
          <span style={{
            padding: '2px 8px',
            border: '1px solid #32363a',
            fontSize: '11px',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
            background: status === 'PENDING' ? '#32363a' : '#fff',
            color: status === 'PENDING' ? '#fff' : '#32363a',
          }}>
            {status}
          </span>
        );
      },
    },
    {
      headerName: 'Actions',
      width: 200,
      cellRenderer: (params) => {
        if (params.data.status !== 'PENDING') {
          return null;
        }
        return (
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              className="btn btn-success"
              onClick={() => handleApprove(params.data)}
              style={{ padding: '4px 8px', fontSize: '11px', fontWeight: '600' }}
            >
              Approve
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleReject(params.data)}
              style={{ padding: '4px 8px', fontSize: '11px', fontWeight: '600' }}
            >
              Reject
            </button>
          </div>
        );
      },
    },
    {
      field: 'refund_amount',
      headerName: 'Refund Amount',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '$0.00',
      cellStyle: { textAlign: 'right', fontWeight: '600' },
    },
    {
      field: 'reason',
      headerName: 'Reason',
      width: 250,
      filter: true,
      cellStyle: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
    },
    {
      field: 'requested_by',
      headerName: 'Requested By',
      width: 120,
      filter: true,
    },
    {
      field: 'requested_at',
      headerName: 'Requested At',
      width: 160,
      filter: true,
      valueFormatter: (params) => params.value ? new Date(params.value).toLocaleString() : '-',
    },
    {
      field: 'approved_by',
      headerName: 'Approved By',
      width: 120,
      filter: true,
    },
    {
      field: 'approved_at',
      headerName: 'Approved At',
      width: 160,
      filter: true,
      valueFormatter: (params) => params.value ? new Date(params.value).toLocaleString() : '-',
    },
    {
      field: 'rejection_reason',
      headerName: 'Rejection Reason',
      width: 200,
      filter: true,
      cellStyle: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
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
    loadReturns();
  }, [statusFilter]);

  async function loadReturns() {
    try {
      setLoading(true);
      const returns = await salesApi.getReturns({ status: statusFilter, limit: 100 });
      setRowData(returns || []);
    } catch (error) {
      console.error('Failed to load returns:', error);
    } finally {
      setLoading(false);
    }
  }

  const handleQuickFilter = () => {
    if (gridRef.current) {
      gridRef.current.api.setQuickFilter('');
    }
  };

  const handleRefresh = () => {
    loadReturns();
  };

  const handleRowClick = (params) => {
    if (params.data.status === 'PENDING') {
      setSelectedReturn(params.data);
      setShowModal(true);
    }
  };

  const handleModalSuccess = () => {
    setShowModal(false);
    setSelectedReturn(null);
    loadReturns();
    alert('Return processed successfully');
  };

  const getRowId = (params) => {
    return params.data.id;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Return Requests (Admin)</h1>
        <div className="action-bar">
          <select
            className="form-input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: '150px' }}
          >
            <option value="PENDING">PENDING</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
          <button className="btn btn-primary" onClick={handleRefresh}>
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
              Loading return requests...
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
              rowSelection={'single'}
              animateRows={false}
              suppressCellFocus={true}
              theme="legacy"
              onRowClick={handleRowClick}
              overlayNoRowsTemplate="&lt;span style=&quot;padding: 40px; color: #718096;&quot;&gt;No return requests found&lt;/span&gt;"
            />
          )}
        </div>
      </div>

      <div style={{ marginTop: '12px', fontSize: '12px', color: '#718096' }}>
        Tip: Click on a PENDING return to approve or reject it
      </div>

      {showModal && selectedReturn && (
        <ReturnDecisionModal
          returnRequest={selectedReturn}
          onClose={() => {
            setShowModal(false);
            setSelectedReturn(null);
          }}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
}
