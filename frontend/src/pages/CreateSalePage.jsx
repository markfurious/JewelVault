import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { stockApi, salesApi } from '../services/api';

export default function CreateSalePage() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [activeItemIndex, setActiveItemIndex] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    payment_method: 'CASH',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      // Filter: only AVAILABLE items can be sold
      const filtered = products.filter(
        (p) =>
          p.status === 'AVAILABLE' &&
          (p.sku.toLowerCase().includes(query) ||
          p.name.toLowerCase().includes(query) ||
          (p.category && p.category.toLowerCase().includes(query)))
      );
      setFilteredProducts(filtered.slice(0, 50));
    } else {
      setFilteredProducts([]);
    }
  }, [searchQuery, products]);

  async function loadProducts() {
    try {
      // Load only AVAILABLE items for sale (item-based model)
      const data = await stockApi.list({ limit: 100, available_only: true });
      setProducts(data.items || []);
    } catch (error) {
      console.error('Failed to load products:', error);
    }
  }

  const selectProduct = (product) => {
    if (activeItemIndex !== null) {
      const newItems = [...selectedItems];
      newItems[activeItemIndex] = {
        ...newItems[activeItemIndex],
        product_id: product.id,
        price: product.retail_price || 0,
      };
      setSelectedItems(newItems);
    }
    setSearchQuery('');
    setShowProductSearch(false);
    setActiveItemIndex(null);
  };

  const addItem = () => {
    setSelectedItems([
      ...selectedItems,
      { product_id: '', quantity: 1, price: 0, discount: 0 },
    ]);
  };

  const updateItem = (index, field, value) => {
    const newItems = [...selectedItems];
    newItems[index] = { ...newItems[index], [field]: value };

    if (field === 'product_id') {
      const product = products.find((p) => p.id === value);
      if (product) {
        newItems[index].price = product.retail_price || 0;
      }
    }

    setSelectedItems(newItems);
  };

  const removeItem = (index) => {
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };

  const calculateTotals = () => {
    const subtotal = selectedItems.reduce(
      (sum, item) => sum + (parseFloat(item.price) || 0) * (parseFloat(item.quantity) || 0),
      0
    );
    const totalDiscount = selectedItems.reduce(
      (sum, item) => sum + (parseFloat(item.discount) || 0),
      0
    );
    const tax = subtotal * 0.08;
    const total = subtotal - totalDiscount + tax;

    return { subtotal, totalDiscount, tax, total };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.customer_name) {
      setError('Customer name is required');
      return;
    }

    if (selectedItems.length === 0) {
      setError('Please add at least one item to the sale');
      return;
    }

    try {
      setLoading(true);

      const saleData = {
        ...formData,
        items: selectedItems.map((item) => ({
          product_id: item.product_id,
          quantity: parseFloat(item.quantity),
          price: parseFloat(item.price),
          discount: parseFloat(item.discount),
        })),
      };

      await salesApi.create(saleData);
      navigate('/sales');
    } catch (err) {
      setError(err.message || 'Failed to create sale');
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">New Sale</h1>
        <button className="btn" onClick={() => navigate('/sales')}>
          ← Back to Sales
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="card mb-16">
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px' }}>
            Customer Information
          </h3>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Customer Name</label>
              <input
                type="text"
                className="form-input"
                value={formData.customer_name}
                onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-input"
                value={formData.customer_email}
                onChange={(e) => setFormData({ ...formData, customer_email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input
                type="text"
                className="form-input"
                value={formData.customer_phone}
                onChange={(e) => setFormData({ ...formData, customer_phone: e.target.value })}
              />
            </div>
          </div>
        </div>

        <div className="card mb-16">
          <div className="flex flex-between mb-16">
            <h3 style={{ fontSize: '14px', fontWeight: '600' }}>Sale Items</h3>
            <button type="button" className="btn btn-primary" onClick={addItem}>
              Add Item
            </button>
          </div>

          {selectedItems.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon" style={{ fontSize: '32px', marginBottom: '12px' }}>📦</div>
              <div className="empty-state-text">No items added. Click "Add Item" to start.</div>
            </div>
          ) : (
            <table className="error-table" style={{ borderBottom: 'none' }}>
              <thead>
                <tr>
                  <th style={{ width: '300px' }}>Product (Search by SKU)</th>
                  <th style={{ width: '100px' }}>Qty</th>
                  <th style={{ width: '120px' }}>Price</th>
                  <th style={{ width: '100px' }}>Discount</th>
                  <th style={{ width: '100px' }}>Subtotal</th>
                  <th style={{ width: '60px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {selectedItems.map((item, index) => {
                  const selectedProduct = products.find((p) => p.id === item.product_id);
                  return (
                    <tr key={index}>
                      <td>
                        <div style={{ position: 'relative' }}>
                          <input
                            type="text"
                            className="form-input form-input-sm"
                            placeholder="Enter SKU or search..."
                            value={
                              activeItemIndex === index && showProductSearch
                                ? searchQuery
                                : selectedProduct
                                ? `${selectedProduct.sku} - ${selectedProduct.name}`
                                : ''
                            }
                            onFocus={() => {
                              setShowProductSearch(true);
                              setActiveItemIndex(index);
                              setSearchQuery('');
                            }}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onBlur={() => {
                              setTimeout(() => {
                                setShowProductSearch(false);
                                setActiveItemIndex(null);
                              }, 200);
                            }}
                          />
                          {showProductSearch && activeItemIndex === index && filteredProducts.length > 0 && (
                            <div
                              style={{
                                position: 'absolute',
                                top: '100%',
                                left: 0,
                                right: 0,
                                background: '#fff',
                                border: '1px solid #e2e8f0',
                                borderRadius: '4px',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                                zIndex: 1000,
                                maxHeight: '300px',
                                overflow: 'auto',
                              }}
                            >
                              {filteredProducts.map((product) => (
                                <div
                                  key={product.id}
                                  onClick={() => selectProduct(product)}
                                  style={{
                                    padding: '8px 12px',
                                    cursor: 'pointer',
                                    borderBottom: '1px solid #f0f0f0',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                  }}
                                  onMouseOver={(e) => (e.currentTarget.style.background = '#f7fafc')}
                                  onMouseOut={(e) => (e.currentTarget.style.background = '#fff')}
                                >
                                  <div>
                                    <div style={{ fontWeight: '600', color: '#2d3748' }}>{product.sku}</div>
                                    <div style={{ fontSize: '12px', color: '#718096' }}>{product.name}</div>
                                  </div>
                                  <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '12px', color: '#276749', fontWeight: '600' }}>AVAILABLE</div>
                                    <div style={{ fontWeight: '600', color: '#276749' }}>
                                      ${(product.retail_price || 0).toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                    <td>
                      <input
                        type="number"
                        className="form-input form-input-sm"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                        min="1"
                        step="0.01"
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        className="form-input form-input-sm"
                        value={item.price}
                        onChange={(e) => updateItem(index, 'price', e.target.value)}
                        min="0"
                        step="0.01"
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        className="form-input form-input-sm"
                        value={item.discount}
                        onChange={(e) => updateItem(index, 'discount', e.target.value)}
                        min="0"
                        step="0.01"
                      />
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: '600' }}>
                      ${((parseFloat(item.price) || 0) * (parseFloat(item.quantity) || 0) - (parseFloat(item.discount) || 0)).toFixed(2)}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={() => removeItem(index)}
                      >
                        ×
                      </button>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="card mb-16">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Payment Method</label>
              <select
                className="form-input"
                value={formData.payment_method}
                onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
              >
                <option value="CASH">Cash</option>
                <option value="CARD">Card</option>
                <option value="CHECK">Check</option>
                <option value="TRANSFER">Bank Transfer</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Notes</label>
              <input
                type="text"
                className="form-input"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Optional notes"
              />
            </div>
          </div>

          <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
            <div className="flex flex-between" style={{ marginBottom: '8px' }}>
              <span>Subtotal:</span>
              <span style={{ fontWeight: '600' }}>${totals.subtotal.toFixed(2)}</span>
            </div>
            <div className="flex flex-between" style={{ marginBottom: '8px', color: '#c53030' }}>
              <span>Discount:</span>
              <span style={{ fontWeight: '600' }}>-${totals.totalDiscount.toFixed(2)}</span>
            </div>
            <div className="flex flex-between" style={{ marginBottom: '8px' }}>
              <span>Tax (8%):</span>
              <span style={{ fontWeight: '600' }}>${totals.tax.toFixed(2)}</span>
            </div>
            <div
              className="flex flex-between"
              style={{
                marginTop: '12px',
                paddingTop: '12px',
                borderTop: '2px solid #e2e8f0',
                fontSize: '18px',
              }}
            >
              <span style={{ fontWeight: '700' }}>Total:</span>
              <span style={{ fontWeight: '700', color: '#276749' }}>${totals.total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="flex gap-16">
          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
            {loading ? 'Processing...' : 'Complete Sale'}
          </button>
          <button type="button" className="btn btn-lg" onClick={() => navigate('/sales')}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
