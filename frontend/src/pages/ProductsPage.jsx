import React, { useState, useCallback, useRef, useEffect } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { stockApi, productsApi } from '../services/api';
import BulkUploadModal from '../components/BulkUploadModal';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

export default function ProductsPage() {
  const gridRef = useRef(null);
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    category: '',
    cost_price: '',
    retail_price: '',
    wholesale_price: '',
    initial_quantity: '',
  });

  const [columnDefs] = useState([
    {
      field: 'sku',
      headerName: 'SKU',
      width: 100,
      pinned: 'left',
      filter: true,
      cellStyle: { fontWeight: '600', color: '#000000' },
    },
    {
      field: 'name',
      headerName: 'Product Name',
      width: 200,
      filter: true,
      cellStyle: { color: '#000000' },
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
      filter: true,
      cellStyle: { color: '#000000' },
    },
    {
      field: 'sub_category',
      headerName: 'Sub Category',
      width: 120,
      filter: true,
      cellStyle: { color: '#000000' },
    },
    {
      field: 'style_number',
      headerName: 'Style Number',
      width: 100,
      filter: true,
      cellStyle: { color: '#000000' },
    },
    {
      field: 'gold_purity',
      headerName: 'Gold Purity',
      width: 100,
      filter: true,
      cellStyle: { color: '#000000' },
      cellRenderer: (params) => params.value ? (
        <span className="badge badge-info">{params.value}</span>
      ) : '-',
    },
    {
      field: 'certified',
      headerName: 'Certified',
      width: 80,
      filter: true,
      cellStyle: { color: '#000000' },
      cellRenderer: (params) => params.value ? (
        <span className="badge badge-success">Yes</span>
      ) : (
        <span className="badge badge-warning">No</span>
      ),
    },
    {
      field: 'status',
      headerName: 'Item Status',
      width: 110,
      filter: true,
      cellStyle: { textAlign: 'center', fontWeight: '600', color: '#000000' },
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
      field: 'retail_price',
      headerName: 'Retail Price',
      width: 100,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '-',
      cellStyle: { textAlign: 'right', fontWeight: '600', color: '#000000' },
    },
    {
      field: 'wholesale_price',
      headerName: 'Wholesale Price',
      width: 110,
      filter: true,
      valueFormatter: (params) => params.value ? `$${parseFloat(params.value).toFixed(2)}` : '-',
      cellStyle: { textAlign: 'right', color: '#000000' },
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 80,
      filter: true,
      cellStyle: { color: '#000000' },
      cellRenderer: (params) => params.value !== false ? (
        <span className="badge badge-success">Active</span>
      ) : (
        <span className="badge badge-danger">Inactive</span>
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

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await stockApi.list({ limit: 1000 });
      setRowData(data.items || []);
    } catch (err) {
      console.error('Failed to load products:', err);
      let errorMsg = 'Failed to load products';
      if (typeof err === 'string') {
        errorMsg = err;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        cost_price: formData.cost_price ? parseFloat(formData.cost_price) : null,
        retail_price: formData.retail_price ? parseFloat(formData.retail_price) : null,
        wholesale_price: formData.wholesale_price ? parseFloat(formData.wholesale_price) : null,
        initial_quantity: formData.initial_quantity ? parseFloat(formData.initial_quantity) : 0,
      };
      await productsApi.create(payload);
      setFormData({
        sku: '',
        name: '',
        category: '',
        cost_price: '',
        retail_price: '',
        wholesale_price: '',
        initial_quantity: '',
      });
      setShowForm(false);
      loadProducts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    try {
      await productsApi.delete(id);
      loadProducts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleBulkUploadSuccess = () => {
    loadProducts();
    setShowUploadModal(false);
  };

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

  const handleRefresh = () => {
    loadProducts();
  };

  const getRowId = useCallback((params) => {
    return params.data.id || params.data.sku;
  }, []);

  if (loading && rowData.length === 0) {
    return (
      <div className="page-container">
        <div className="loading">
          <div className="loading-spinner"></div>
          Loading products...
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Products Management</h1>
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
          <button className="btn btn-success" onClick={() => setShowUploadModal(true)}>
            📤 Bulk Upload
          </button>
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '➕ Add Product'}
          </button>
          <button className="btn btn-primary" onClick={handleRefresh}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {showForm && (
        <div className="card mb-16">
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px' }}>New Product</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">SKU *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Category</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Initial Quantity</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.initial_quantity}
                  onChange={(e) => setFormData({ ...formData, initial_quantity: e.target.value })}
                  min="0"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Cost Price</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.cost_price}
                  onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Retail Price</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.retail_price}
                  onChange={(e) => setFormData({ ...formData, retail_price: e.target.value })}
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Wholesale Price</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.wholesale_price}
                  onChange={(e) => setFormData({ ...formData, wholesale_price: e.target.value })}
                  min="0"
                  step="0.01"
                />
              </div>
            </div>
            <button type="submit" className="btn btn-success">Create Product</button>
          </form>
        </div>
      )}

      <div className="ag-grid-container">
        <div
          className="ag-theme-alpine"
          style={{ width: '100%', height: 'calc(100vh - 220px)' }}
        >
          {rowData.length === 0 && !loading ? (
            <div className="empty-state">
              <div className="empty-state-icon">📦</div>
              <div className="empty-state-text">No products found. Add products manually or use bulk upload.</div>
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
              onGridReady={onGridReady}
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
