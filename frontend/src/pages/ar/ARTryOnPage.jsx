/**
 * AR Try-On Page
 * Main page for virtual jewelry try-on experience
 */
import React, { useState, useEffect, useCallback } from 'react';
import FaceMeshAR from '../../components/ar/FaceMeshAR';

const API_BASE = '/api/v1';

async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = localStorage.getItem('access_token');
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      let errorData;
      try { errorData = await response.json(); } catch { errorData = { detail: `HTTP ${response.status}` }; }
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

export default function ARTryOnPage() {
  const [jewelryList, setJewelryList] = useState([]);
  const [selectedJewelry, setSelectedJewelry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isARActive, setIsARActive] = useState(false);
  const [screenshotCaptured, setScreenshotCaptured] = useState(null);
  const [tryOnStartTime, setTryOnStartTime] = useState(null);
  const [getScreenshotFn, setGetScreenshotFn] = useState(null);

  // Generate session ID for tracking
  const sessionId = useCallback(() => {
    if (!window.__arSessionId) {
      window.__arSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    return window.__arSessionId;
  }, []);

  // Fetch jewelry list
  useEffect(() => {
    loadJewelry();
  }, []);

  const loadJewelry = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchApi('/jewelry?type=earring');
      setJewelryList(data.items || []);
      if (data.items && data.items.length > 0) {
        setSelectedJewelry(data.items[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load jewelry');
    } finally {
      setLoading(false);
    }
  };

  // Start AR session
  const startARSession = () => {
    setIsARActive(true);
    setTryOnStartTime(Date.now());
  };

  // Stop AR session
  const stopARSession = () => {
    setIsARActive(false);
    logTryOnEvent();
  };

  // Log try-on event to backend
  const logTryOnEvent = async () => {
    if (!selectedJewelry || !tryOnStartTime) return;

    try {
      const duration = Math.floor((Date.now() - tryOnStartTime) / 1000);
      await fetchApi('/jewelry/tryon/log', {
        method: 'POST',
        body: JSON.stringify({
          product_id: selectedJewelry.id,
          session_id: sessionId(),
          screenshot_url: screenshotCaptured,
          duration_seconds: duration,
        }),
      });
    } catch (err) {
      console.error('Failed to log try-on event:', err);
    }
  };

  // Handle screenshot capture
  const handleScreenshot = useCallback((getScreenshotFn) => {
    setGetScreenshotFn(() => getScreenshotFn);
  }, []);

  // Capture and save screenshot
  const captureScreenshot = async () => {
    if (!getScreenshotFn) return;

    try {
      const dataUrl = getScreenshotFn();
      if (dataUrl) {
        setScreenshotCaptured(dataUrl);

        // Create download link
        const link = document.createElement('a');
        link.download = `tryon-${selectedJewelry?.name || 'jewelry'}-${Date.now()}.png`;
        link.href = dataUrl;
        link.click();

        // Log the screenshot
        logTryOnEvent();
      }
    } catch (err) {
      alert('Failed to capture screenshot');
    }
  };

  // Handle jewelry selection
  const handleSelectJewelry = (jewelry) => {
    setSelectedJewelry(jewelry);
    setScreenshotCaptured(null);
  };

  return (
    <div className="page-container" style={{ paddingBottom: '20px' }}>
      <div className="page-header">
        <h1 className="page-title">Virtual Try-On</h1>
        <div className="action-bar">
          {!isARActive ? (
            <button className="btn btn-primary" onClick={startARSession}>
              Start AR Try-On
            </button>
          ) : (
            <>
              <button className="btn" onClick={captureScreenshot}>
                📷 Capture
              </button>
              <button className="btn btn-danger" onClick={stopARSession}>
                End Session
              </button>
            </>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px', height: 'calc(100vh - 180px)' }}>
        {/* AR View */}
        <div style={{ background: '#000', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
          {!isARActive ? (
            <div style={styles.arPlaceholder}>
              <div style={{ fontSize: '64px', marginBottom: '20px' }}>💎</div>
              <h2 style={{ margin: '0 0 10px 0', color: '#fff' }}>Ready to Try On?</h2>
              <p style={{ color: '#888', marginBottom: '20px' }}>
                Allow camera access to see jewelry on yourself
              </p>
              <button className="btn btn-primary" onClick={startARSession}>
                Start AR Experience
              </button>
            </div>
          ) : (
            <FaceMeshAR
              jewelry={selectedJewelry}
              jewelryType="earring"
              onScreenshot={handleScreenshot}
              isActive={isARActive}
            />
          )}

          {/* Screenshot preview */}
          {screenshotCaptured && (
            <div style={styles.screenshotPreview}>
              <img src={screenshotCaptured} alt="Screenshot" style={{ maxWidth: '200px', borderRadius: '4px' }} />
              <p style={{ fontSize: '12px', color: '#888', marginTop: '8px' }}>Screenshot saved!</p>
            </div>
          )}
        </div>

        {/* Jewelry Selection Panel */}
        <div style={{ background: '#fff', borderRadius: '8px', padding: '16px', overflowY: 'auto' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>Select Jewelry</h3>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
              Loading jewelry...
            </div>
          ) : error ? (
            <div style={{ padding: '20px', color: '#dc2626', background: '#fef2f2', borderRadius: '4px' }}>
              {error}
              <button className="btn btn-sm" onClick={loadJewelry} style={{ marginTop: '10px' }}>
                Retry
              </button>
            </div>
          ) : jewelryList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
              No jewelry available
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {jewelryList.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectJewelry(item)}
                  style={{
                    ...styles.jewelryCard,
                    ...(selectedJewelry?.id === item.id ? styles.jewelryCardSelected : {}),
                  }}
                >
                  <div style={{ width: '60px', height: '60px', background: '#f3f4f6', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {item.thumbnail_url ? (
                      <img src={item.thumbnail_url} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '4px' }} />
                    ) : (
                      <span style={{ fontSize: '24px' }}>💎</span>
                    )}
                  </div>
                  <div style={{ flex: 1, marginLeft: '12px' }}>
                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '500' }}>{item.name}</h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#059669', fontWeight: '600' }}>
                      ${parseFloat(item.price).toFixed(2)}
                    </p>
                  </div>
                  {selectedJewelry?.id === item.id && (
                    <div style={{ color: '#2563eb', fontSize: '20px' }}>✓</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Session info */}
          {isARActive && (
            <div style={{ marginTop: '20px', padding: '12px', background: '#f3f4f6', borderRadius: '4px' }}>
              <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
                <strong>Session:</strong> {sessionId().slice(0, 20)}...
              </p>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#666' }}>
                <strong>Duration:</strong> {tryOnStartTime ? Math.floor((Date.now() - tryOnStartTime) / 1000) : 0}s
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  arPlaceholder: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    minHeight: '500px',
    background: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
  },
  jewelryCard: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px',
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  jewelryCardSelected: {
    borderColor: '#2563eb',
    background: '#eff6ff',
    boxShadow: '0 2px 8px rgba(37, 99, 235, 0.2)',
  },
  screenshotPreview: {
    position: 'absolute',
    bottom: '20px',
    right: '20px',
    background: 'rgba(0, 0, 0, 0.8)',
    padding: '12px',
    borderRadius: '8px',
    textAlign: 'center',
  },
};
