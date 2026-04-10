import React, { useState, useRef } from 'react';

export default function BulkUploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.match(/\.(xlsx|xls|csv)$/)) {
        setError('Please select a valid Excel file (.xlsx, .xls) or CSV file');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (!droppedFile.name.match(/\.(xlsx|xls|csv)$/)) {
        setError('Please select a valid Excel file (.xlsx, .xls) or CSV file');
        return;
      }
      setFile(droppedFile);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('initial_quantity', '0');

      const response = await fetch('/api/v1/products/bulk-upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(`Successfully uploaded ${data.records_created} products!`);
        setUploadResult(data);
        setTimeout(() => {
          onSuccess();
        }, 1500);
      } else {
        setError({
          message: 'Upload failed with validation errors',
          details: data.detail || [],
        });
      }
    } catch (err) {
      setError({
        message: err.message || 'Upload failed. Please try again.',
        details: [],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
        <div className="modal-header">
          <h2 className="modal-title">Bulk Upload Products</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {!success && (
            <>
              <div
                className="file-upload"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="file-upload-icon">📁</div>
                <div className="file-upload-text">
                  {file ? file.name : 'Click to select or drag and drop Excel file here'}
                </div>
                <div className="file-upload-hint">
                  Supported formats: .xlsx, .xls (max 10MB)
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileSelect}
                />
              </div>

              {file && (
                <div className="mt-16">
                  <div className="alert alert-warning">
                    <strong>⚠️ Important:</strong> All rows will be validated before upload.
                    If any row fails validation, the entire file will be rejected.
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-16">
                  <div className="alert alert-error">
                    <strong>{error.message}</strong>
                  </div>

                  {error.details && error.details.length > 0 && (
                    <div style={{ marginTop: '12px' }}>
                      <h4 style={{ fontSize: '13px', fontWeight: '600', marginBottom: '8px', color: '#c53030' }}>
                        Validation Errors:
                      </h4>
                      <table className="error-table">
                        <thead>
                          <tr>
                            <th>Row</th>
                            <th>Column</th>
                            <th>Error</th>
                          </tr>
                        </thead>
                        <tbody>
                          {error.details.slice(0, 50).map((err, idx) => (
                            <tr key={idx}>
                              <td>{err.row || '-'}</td>
                              <td>{err.column || '-'}</td>
                              <td>{err.error || err.message || 'Unknown error'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {error.details.length > 50 && (
                        <p style={{ fontSize: '11px', color: '#718096', marginTop: '8px' }}>
                          ... and {error.details.length - 50} more errors
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {success && (
            <div className="alert alert-success" style={{ textAlign: 'center', padding: '32px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#276749' }}>
                {success}
              </h3>
              <p style={{ fontSize: '13px', color: '#68d391', marginTop: '8px' }}>
                Redirecting to stock view...
              </p>
            </div>
          )}
        </div>

        {!success && (
          <div className="modal-footer">
            <button className="btn" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={loading || !file}
            >
              {loading ? (
                <>
                  <span className="loading-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px', marginRight: '8px' }}></span>
                  Uploading...
                </>
              ) : (
                <>
                  📤 Upload Products
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
