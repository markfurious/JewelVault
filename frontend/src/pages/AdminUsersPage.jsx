import React, { useState, useEffect } from 'react';
import { authApi, companiesApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

function AdminUsersPage() {
  const { user: currentUser, isSuperAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('users');

  // User form state
  const [showUserForm, setShowUserForm] = useState(false);
  const [userFormData, setUserFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'company_user',
    company_id: '',
  });

  // Company form state
  const [showCompanyForm, setShowCompanyForm] = useState(false);
  const [companyFormData, setCompanyFormData] = useState({
    name: '',
    code: '',
    address: '',
    phone: '',
    email: '',
    tax_id: '',
    currency: 'USD',
    timezone: 'UTC',
  });

  useEffect(() => {
    if (!isSuperAdmin()) {
      setError('Super Admin access required');
      return;
    }
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersData, companiesData] = await Promise.all([
        authApi.getUsers(),
        companiesApi.list({ limit: 100 }),
      ]);
      setUsers(usersData);
      setCompanies(companiesData.items || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // User handlers
  const handleUserSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = { ...userFormData };
      if (!submitData.company_id) {
        delete submitData.company_id;
      }
      await authApi.register(submitData);
      setUserFormData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'company_user',
        company_id: '',
      });
      setShowUserForm(false);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await authApi.changeUserRole(userId, newRole);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleActive = async (userId) => {
    try {
      await authApi.toggleUserActive(userId);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleLocked = async (userId) => {
    try {
      await authApi.toggleUserLocked(userId);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await authApi.deleteUser(userId);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  // Company handlers
  const handleCompanySubmit = async (e) => {
    e.preventDefault();
    try {
      await companiesApi.create(companyFormData);
      setCompanyFormData({
        name: '',
        code: '',
        address: '',
        phone: '',
        email: '',
        tax_id: '',
        currency: 'USD',
        timezone: 'UTC',
      });
      setShowCompanyForm(false);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleCompanyActive = async (companyId) => {
    try {
      const company = companies.find(c => c.id === companyId);
      await companiesApi.update(companyId, { is_active: !company.is_active });
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteCompany = async (companyId) => {
    if (!confirm('Are you sure you want to delete this company? This will affect all users in this company.')) return;
    try {
      await companiesApi.delete(companyId);
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? company.name : '-';
  };

  if (!isSuperAdmin()) {
    return (
      <div className="alert alert-error">
        Super Admin access required. You do not have permission to view this page.
      </div>
    );
  }

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div>
      <div className="page-header" style={{ marginBottom: '20px' }}>
        <h1>Admin Management</h1>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '2px solid #e0e0e0', paddingBottom: '8px' }}>
        <button
          className={`btn ${activeTab === 'users' ? 'btn-primary' : 'btn'}`}
          onClick={() => setActiveTab('users')}
          style={{ borderRadius: '6px 6px 0 0' }}
        >
          Users
        </button>
        <button
          className={`btn ${activeTab === 'companies' ? 'btn-primary' : 'btn'}`}
          onClick={() => setActiveTab('companies')}
          style={{ borderRadius: '6px 6px 0 0' }}
        >
          Companies
        </button>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: '16px' }}>{error}</div>}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <>
          <div className="flex-between mb-20">
            <h2>User Management</h2>
            <button
              className="btn btn-primary"
              onClick={() => setShowUserForm(!showUserForm)}
            >
              {showUserForm ? 'Cancel' : 'Add User'}
            </button>
          </div>

          {showUserForm && (
            <div className="card" style={{ marginBottom: '20px' }}>
              <h3>New User</h3>
              <form onSubmit={handleUserSubmit}>
                <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label>Username *</label>
                    <input
                      type="text"
                      value={userFormData.username}
                      onChange={(e) => setUserFormData({ ...userFormData, username: e.target.value })}
                      required
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div className="form-group">
                    <label>Email *</label>
                    <input
                      type="email"
                      value={userFormData.email}
                      onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                      required
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label>Password *</label>
                    <input
                      type="password"
                      value={userFormData.password}
                      onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
                      required
                      minLength="6"
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      value={userFormData.full_name}
                      onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label>Role *</label>
                    <select
                      value={userFormData.role}
                      onChange={(e) => setUserFormData({ ...userFormData, role: e.target.value })}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="company_user">Company User</option>
                      <option value="company_admin">Company Admin</option>
                      <option value="super_admin">Super Admin</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Company</label>
                    <select
                      value={userFormData.company_id}
                      onChange={(e) => setUserFormData({ ...userFormData, company_id: e.target.value })}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="">No Company</option>
                      {companies.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <button type="submit" className="btn btn-success" style={{ marginTop: '12px' }}>Create User</button>
              </form>
            </div>
          )}

          <div className="card">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Full Name</th>
                    <th>Company</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="empty-state">No users found</td>
                    </tr>
                  ) : (
                    users.map((u) => (
                      <tr key={u.id}>
                        <td>
                          <strong>{u.username}</strong>
                          {u.id === currentUser?.id && (
                            <span style={{ marginLeft: '8px', fontSize: '11px', color: '#888' }}>(You)</span>
                          )}
                        </td>
                        <td>{u.email}</td>
                        <td>{u.full_name || '-'}</td>
                        <td>{getCompanyName(u.company_id)}</td>
                        <td>
                          <select
                            value={u.role}
                            onChange={(e) => handleRoleChange(u.id, e.target.value)}
                            style={{ padding: '4px 8px', fontSize: '13px' }}
                          >
                            <option value="company_user">Company User</option>
                            <option value="company_admin">Company Admin</option>
                            <option value="super_admin">Super Admin</option>
                          </select>
                        </td>
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <input
                                type="checkbox"
                                checked={u.is_active}
                                onChange={() => handleToggleActive(u.id)}
                              />
                              Active
                            </label>
                            <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <input
                                type="checkbox"
                                checked={u.is_locked}
                                onChange={() => handleToggleLocked(u.id)}
                              />
                              Locked
                            </label>
                          </div>
                        </td>
                        <td>
                          {u.last_login
                            ? new Date(u.last_login).toLocaleString()
                            : 'Never'}
                        </td>
                        <td>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            onClick={() => handleDeleteUser(u.id)}
                            disabled={u.id === currentUser?.id}
                          >
                            {u.id === currentUser?.id ? 'Cannot Delete' : 'Delete'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Companies Tab */}
      {activeTab === 'companies' && (
        <>
          <div className="flex-between mb-20">
            <h2>Company Management</h2>
            <button
              className="btn btn-primary"
              onClick={() => setShowCompanyForm(!showCompanyForm)}
            >
              {showCompanyForm ? 'Cancel' : 'Add Company'}
            </button>
          </div>

          {showCompanyForm && (
            <div className="card" style={{ marginBottom: '20px' }}>
              <h3>New Company</h3>
              <form onSubmit={handleCompanySubmit}>
                <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label>Company Name *</label>
                    <input
                      type="text"
                      value={companyFormData.name}
                      onChange={(e) => setCompanyFormData({ ...companyFormData, name: e.target.value })}
                      required
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div className="form-group">
                    <label>Company Code *</label>
                    <input
                      type="text"
                      value={companyFormData.code}
                      onChange={(e) => setCompanyFormData({ ...companyFormData, code: e.target.value })}
                      required
                      placeholder="e.g., ACME, CORP1"
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label>Email</label>
                    <input
                      type="email"
                      value={companyFormData.email}
                      onChange={(e) => setCompanyFormData({ ...companyFormData, email: e.target.value })}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div className="form-group">
                    <label>Phone</label>
                    <input
                      type="text"
                      value={companyFormData.phone}
                      onChange={(e) => setCompanyFormData({ ...companyFormData, phone: e.target.value })}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label>Currency</label>
                    <select
                      value={companyFormData.currency}
                      onChange={(e) => setCompanyFormData({ ...companyFormData, currency: e.target.value })}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="USD">USD - US Dollar</option>
                      <option value="EUR">EUR - Euro</option>
                      <option value="GBP">GBP - British Pound</option>
                      <option value="INR">INR - Indian Rupee</option>
                      <option value="AED">AED - UAE Dirham</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Timezone</label>
                    <input
                      type="text"
                      value={companyFormData.timezone}
                      onChange={(e) => setCompanyFormData({ ...companyFormData, timezone: e.target.value })}
                      placeholder="UTC"
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Address</label>
                  <textarea
                    value={companyFormData.address}
                    onChange={(e) => setCompanyFormData({ ...companyFormData, address: e.target.value })}
                    rows={2}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                </div>
                <div className="form-group">
                  <label>Tax ID</label>
                  <input
                    type="text"
                    value={companyFormData.tax_id}
                    onChange={(e) => setCompanyFormData({ ...companyFormData, tax_id: e.target.value })}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                </div>
                <button type="submit" className="btn btn-success" style={{ marginTop: '12px' }}>Create Company</button>
              </form>
            </div>
          )}

          <div className="card">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Code</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Currency</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="empty-state">No companies found</td>
                    </tr>
                  ) : (
                    companies.map((c) => (
                      <tr key={c.id}>
                        <td><strong>{c.name}</strong></td>
                        <td><code>{c.code}</code></td>
                        <td>{c.email || '-'}</td>
                        <td>{c.phone || '-'}</td>
                        <td>{c.currency}</td>
                        <td>
                          <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <input
                              type="checkbox"
                              checked={c.is_active}
                              onChange={() => handleToggleCompanyActive(c.id)}
                            />
                            {c.is_active ? 'Active' : 'Inactive'}
                          </label>
                        </td>
                        <td>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            onClick={() => handleDeleteCompany(c.id)}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default AdminUsersPage;
