import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function LoginPage() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(formData.username, formData.password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated background circles */}
      <div style={{
        position: 'absolute',
        width: '300px',
        height: '300px',
        borderRadius: '50%',
        background: 'rgba(233, 69, 96, 0.1)',
        top: '10%',
        left: '20%',
        animation: 'float 6s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute',
        width: '200px',
        height: '200px',
        borderRadius: '50%',
        background: 'rgba(233, 69, 96, 0.08)',
        bottom: '15%',
        right: '15%',
        animation: 'float 8s ease-in-out infinite reverse',
      }} />

      <div style={{
        width: '100%',
        maxWidth: '340px',
        padding: '40px 32px',
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.1)',
        backdropFilter: 'blur(10px)',
        position: 'relative',
        zIndex: 1,
      }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '56px',
            height: '56px',
            margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #e94560 0%, #0f3460 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(233, 69, 96, 0.4)',
          }}>
            <span style={{ fontSize: '24px' }}>📦</span>
          </div>
          <h1 style={{ fontSize: '20px', marginBottom: '6px', color: '#1a1a2e', fontWeight: '700' }}>
            Inventory System
          </h1>
          <p style={{ fontSize: '13px', color: '#666' }}>Sign in to continue</p>
        </div>

        {error && (
          <div style={{ marginBottom: '16px', padding: '10px 14px', background: '#fee', borderRadius: '8px', fontSize: '13px', color: '#c00', border: '1px solid #fcc' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="Username"
              required
              autoComplete="off"
              style={{
                width: '100%',
                padding: '12px 14px',
                border: '2px solid #e8e8e8',
                borderRadius: '10px',
                fontSize: '14px',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'all 0.2s',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#e94560';
                e.target.style.boxShadow = '0 0 0 3px rgba(233, 69, 96, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e8e8e8';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Password"
              required
              autoComplete="current-password"
              style={{
                width: '100%',
                padding: '12px 14px',
                border: '2px solid #e8e8e8',
                borderRadius: '10px',
                fontSize: '14px',
                boxSizing: 'border-box',
                outline: 'none',
                transition: 'all 0.2s',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#e94560';
                e.target.style.boxShadow = '0 0 0 3px rgba(233, 69, 96, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e8e8e8';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              fontWeight: '600',
              color: '#fff',
              background: loading ? '#ccc' : 'linear-gradient(135deg, #e94560 0%, #0f3460 100%)',
              border: 'none',
              borderRadius: '10px',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: loading ? 'none' : '0 4px 12px rgba(233, 69, 96, 0.3)',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(233, 69, 96, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 12px rgba(233, 69, 96, 0.3)';
              }
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(10deg); }
        }
      `}</style>
    </div>
  );
}

export default LoginPage;
