import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const { user, isSuperAdmin } = useAuth();
  const navigate = useNavigate();
  const [showAdminDropdown, setShowAdminDropdown] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  const isSuperAdminUser = isSuperAdmin();

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="navbar-brand">JewelVault</div>
        <ul className="navbar-menu">
          <li>
            <NavLink to="/" end={({ isActive }) => isActive ? 'active' : ''}>
              Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/stock" end={({ isActive }) => isActive ? 'active' : ''}>
              Stock
            </NavLink>
          </li>
          <li>
            <NavLink to="/sales" end={({ isActive }) => isActive ? 'active' : ''}>
              Sales
            </NavLink>
          </li>
          <li>
            <NavLink to="/ar-tryon" end={({ isActive }) => isActive ? 'active' : ''}>
              AR Try-On
            </NavLink>
          </li>
          {isSuperAdminUser && (
            <li style={{ position: 'relative' }}>
              <button
                onClick={() => setShowAdminDropdown(!showAdminDropdown)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'inherit',
                  cursor: 'pointer',
                  padding: '8px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                Admin ▼
              </button>
              {showAdminDropdown && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  background: '#fff',
                  borderRadius: '6px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  minWidth: '180px',
                  zIndex: 1000,
                  overflow: 'hidden',
                }}>
                  <NavLink
                    to="/admin/users"
                    onClick={() => setShowAdminDropdown(false)}
                    style={{
                      display: 'block',
                      padding: '10px 16px',
                      color: '#333',
                      textDecoration: 'none',
                      borderBottom: '1px solid #eee',
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#f5f5f5'}
                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  >
                    Users & Companies
                  </NavLink>
                  <NavLink
                    to="/admin/returns"
                    onClick={() => setShowAdminDropdown(false)}
                    style={{
                      display: 'block',
                      padding: '10px 16px',
                      color: '#333',
                      textDecoration: 'none',
                      borderBottom: '1px solid #eee',
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#f5f5f5'}
                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  >
                    Returns
                  </NavLink>
                  <NavLink
                    to="/admin/generate-3d"
                    onClick={() => setShowAdminDropdown(false)}
                    style={{
                      display: 'block',
                      padding: '10px 16px',
                      color: '#333',
                      textDecoration: 'none',
                      borderBottom: '1px solid #eee',
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#f5f5f5'}
                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  >
                    Generate 3D Models
                  </NavLink>
                  <NavLink
                    to="/admin/metal-prices"
                    onClick={() => setShowAdminDropdown(false)}
                    style={{
                      display: 'block',
                      padding: '10px 16px',
                      color: '#333',
                      textDecoration: 'none',
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#f5f5f5'}
                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  >
                    Metal Prices
                  </NavLink>
                </div>
              )}
            </li>
          )}
        </ul>
        <div className="navbar-actions">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', marginRight: '8px' }}>
            <span className="user-info" style={{ fontWeight: '600' }}>{user?.username || 'User'}</span>
            <span style={{ fontSize: '11px', color: '#666' }}>{user?.company?.name || 'No Company'}</span>
          </div>
          <button className="btn btn-sm btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>
      {children}
    </div>
  );
}
