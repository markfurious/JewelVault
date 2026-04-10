import React, { useState, useEffect } from 'react';
import { jewelryApi } from '../../services/api';

function Generate3DModelsPage() {
  const [generatorStatus, setGeneratorStatus] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResults, setGenerationResults] = useState(null);
  const [error, setError] = useState(null);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState([]);
  const [excelFile, setExcelFile] = useState(null);
  const [isProcessingExcel, setIsProcessingExcel] = useState(false);
  const [excelResults, setExcelResults] = useState(null);

  useEffect(() => {
    checkGeneratorStatus();
  }, []);

  const checkGeneratorStatus = async () => {
    try {
      const status = await jewelryApi.check3DGenerator();
      setGeneratorStatus(status);
    } catch (err) {
      setError('Failed to check 3D generator status: ' + err.message);
    }
  };

  const handleGenerateBatch = async () => {
    setIsGenerating(true);
    setError(null);
    setGenerationResults(null);

    try {
      const results = await jewelryApi.generate3DBatch();
      setGenerationResults(results);
    } catch (err) {
      setError('Batch generation failed: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setUploadFiles(files);
  };

  const handleUploadAndGenerate = async () => {
    if (uploadFiles.length === 0) {
      setError('Please select files first');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setUploadProgress([]);

    try {
      // Upload images first (you'll need to add this endpoint)
      // Then trigger batch generation
      const results = await jewelryApi.generate3DBatch();
      setGenerationResults(results);
    } catch (err) {
      setError('Upload and generation failed: ' + err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExcelFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setExcelFile(file);
      setError(null);
    }
  };

  const handleUploadExcelAndGenerate = async () => {
    if (!excelFile) {
      setError('Please select an Excel file first');
      return;
    }

    setIsProcessingExcel(true);
    setError(null);
    setExcelResults(null);

    try {
      const formData = new FormData();
      formData.append('file', excelFile);

      const results = await jewelryApi.uploadExcelAndGenerate(formData);
      setExcelResults(results);
    } catch (err) {
      setError('Excel processing failed: ' + err.message);
    } finally {
      setIsProcessingExcel(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await fetch('/api/v1/jewelry/download-template', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to download template');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'jewelry_3d_template.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download template: ' + err.message);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>3D Model Generator</h1>
      <p style={styles.description}>
        Generate 3D models from product photos using TripoSR (self-hosted AI).
        Batch process all jewelry items that have thumbnails but no 3D models.
      </p>

      {/* Generator Status */}
      <div style={styles.statusCard}>
        <h2 style={styles.subheading}>Generator Status</h2>
        {generatorStatus ? (
          <div style={styles.statusContent}>
            <div style={getStatusStyle(generatorStatus.tripors_installed)}>
              <strong>TripoSR Installed:</strong> {generatorStatus.tripors_installed ? 'Yes' : 'No'}
            </div>
            {generatorStatus.tripors_path && (
              <div style={styles.statusRow}>
                <strong>Installation Path:</strong> <code>{generatorStatus.tripors_path}</code>
              </div>
            )}
            <div style={styles.statusRow}>
              <strong>Using Fallback:</strong> {generatorStatus.using_fallback ? 'Yes (CPU mode)' : 'No'}
            </div>
            {generatorStatus.fallback_generator && (
              <div style={styles.statusRow}>
                <strong>Fallback:</strong> {generatorStatus.fallback_generator}
              </div>
            )}
            <div style={{...styles.recommendation, marginTop: '16px'}}>
              <strong>Recommendation:</strong> {generatorStatus.recommendation}
            </div>
          </div>
        ) : (
          <p>Loading status...</p>
        )}
      </div>

      {/* Batch Generation */}
      <div style={styles.actionCard}>
        <h2 style={styles.subheading}>Batch Generate 3D Models</h2>
        <p style={styles.actionDescription}>
          Process all jewelry items in the database that have thumbnail images but no 3D models yet.
          Models are saved locally and database is updated automatically.
        </p>

        {error && <div style={styles.error}>{error}</div>}

        <button
          onClick={handleGenerateBatch}
          disabled={isGenerating}
          style={isGenerating ? styles.buttonDisabled : styles.button}
        >
          {isGenerating ? 'Generating...' : 'Generate All 3D Models'}
        </button>

        {isGenerating && (
          <div style={styles.loading}>
            <div style={styles.spinner}></div>
            <p>Generating 3D models... This may take 5-10 minutes per item on CPU.</p>
          </div>
        )}
      </div>

      {/* Excel Upload */}
      <div style={styles.actionCard}>
        <h2 style={styles.subheading}>Upload Excel with S3 URLs</h2>
        <p style={styles.actionDescription}>
          Upload an Excel file with product image URLs (S3 or any HTTP URL).
          The system will download images, generate 3D models, and create jewelry records automatically.
        </p>

        <div style={styles.excelInfo}>
          <strong>Required columns:</strong>
          <ul style={{margin: '8px 0', paddingLeft: '20px'}}>
            <li><code>sku</code> - Unique SKU number starting with SI (e.g., SI-001, SI001)</li>
            <li><code>name</code> - Jewelry name</li>
            <li><code>description</code> - Product description</li>
            <li><code>image_url</code> or <code>image_link</code> - URL to product image (S3 or HTTP)</li>
          </ul>
          <strong>Optional columns:</strong>
          <ul style={{margin: '8px 0', paddingLeft: '20px'}}>
            <li><code>type</code> - earring, ring, necklace (default: earring)</li>
            <li><code>price</code> - Price in currency units</li>
          </ul>
        </div>

        <button
          onClick={handleDownloadTemplate}
          style={styles.downloadBtn}
          onMouseEnter={(e) => {
            e.target.style.background = '#047857';
            e.target.style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#059669';
            e.target.style.transform = 'translateY(0)';
          }}
        >
          Download Excel Template
        </button>

        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleExcelFileChange}
          style={styles.fileInput}
        />

        {excelFile && (
          <div style={styles.fileSelected}>
            Selected: <strong>{excelFile.name}</strong>
          </div>
        )}

        <button
          onClick={handleUploadExcelAndGenerate}
          disabled={isProcessingExcel || !excelFile}
          style={(isProcessingExcel || !excelFile) ? styles.buttonDisabled : styles.button}
        >
          {isProcessingExcel ? 'Processing...' : 'Upload Excel & Generate 3D Models'}
        </button>

        {isProcessingExcel && (
          <div style={styles.loading}>
            <div style={styles.spinner}></div>
            <p>Downloading images and generating 3D models... This may take several minutes.</p>
          </div>
        )}
      </div>

      {/* Results */}
      {generationResults && (
        <div style={styles.resultsCard}>
          <h2 style={styles.subheading}>Batch Generation Results</h2>
          <div style={styles.summary}>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Total Processed:</span>
              <span style={styles.summaryValue}>{generationResults.total_processed}</span>
            </div>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Success:</span>
              <span style={{...styles.summaryValue, color: '#16a34a'}}>{generationResults.success}</span>
            </div>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Failed:</span>
              <span style={{...styles.summaryValue, color: '#dc2626'}}>{generationResults.failed}</span>
            </div>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>No Image:</span>
              <span style={{...styles.summaryValue, color: '#6b7280'}}>{generationResults.no_image}</span>
            </div>
          </div>

          <div style={styles.resultsList}>
            {generationResults.results?.map((result, index) => (
              <div key={index} style={getResultStyle(result.status)}>
                <div style={styles.resultHeader}>
                  <span style={styles.resultName}>{result.name}</span>
                  <span style={getResultBadgeStyle(result.status)}>
                    {result.status === 'success' ? '✓ Success' : result.status === 'failed' ? '✗ Failed' : 'No Image'}
                  </span>
                </div>
                {result.model_url && (
                  <div style={styles.resultDetail}>
                    Model: <code>{result.model_url}</code>
                  </div>
                )}
                {result.reason && (
                  <div style={styles.resultDetail}>
                    Reason: {result.reason}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Excel Results */}
      {excelResults && (
        <div style={styles.resultsCard}>
          <h2 style={styles.subheading}>Excel Processing Results</h2>
          <div style={styles.summary}>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Total Processed:</span>
              <span style={styles.summaryValue}>{excelResults.total_processed}</span>
            </div>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Success:</span>
              <span style={{...styles.summaryValue, color: '#16a34a'}}>{excelResults.success}</span>
            </div>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Failed:</span>
              <span style={{...styles.summaryValue, color: '#dc2626'}}>{excelResults.failed}</span>
            </div>
          </div>

          <div style={styles.resultsList}>
            {excelResults.results?.map((result, index) => (
              <div key={index} style={getResultStyle(result.status)}>
                <div style={styles.resultHeader}>
                  <span style={styles.resultName}>Row {result.row}: {result.name}</span>
                  <span style={getResultBadgeStyle(result.status)}>
                    {result.status === 'success' ? '✓ Success' :
                     result.status === 'download_failed' ? '✗ Download Failed' :
                     result.status === 'generation_failed' ? '✗ Generation Failed' : '✗ Error'}
                  </span>
                </div>
                {result.model_url && (
                  <div style={styles.resultDetail}>
                    Model: <code>{result.model_url}</code>
                  </div>
                )}
                {result.jewelry_id && (
                  <div style={styles.resultDetail}>
                    Jewelry ID: <code>{result.jewelry_id}</code>
                  </div>
                )}
                {result.error && (
                  <div style={styles.resultDetail}>
                    Error: {result.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Installation Guide */}
      <div style={styles.guideCard}>
        <h2 style={styles.subheading}>Installing TripoSR</h2>
        <p style={styles.guideDescription}>
          For best quality 3D models, install TripoSR locally. Requires NVIDIA GPU with 8GB+ VRAM.
        </p>
        <div style={styles.codeBlock}>
          <pre>{`# Clone TripoSR repository
git clone https://github.com/VAST-AI-Research/TripoSR.git /opt/TripoSR
cd /opt/TripoSR

# Install dependencies
pip install -r requirements.txt

# Test installation
python infer.py --help

# Set environment variable if using custom path
export TRIPOR_PATH=/your/custom/path`}</pre>
        </div>
        <p style={{...styles.guideDescription, marginTop: '12px'}}>
          <strong>Note:</strong> Without TripoSR, the system falls back to stable-fast-3d which works on CPU but produces lower quality models.
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1000px',
    margin: '0 auto',
    padding: '24px',
  },
  heading: {
    fontSize: '28px',
    fontWeight: '700',
    marginBottom: '8px',
    color: '#1a1a2e',
  },
  description: {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '24px',
  },
  subheading: {
    fontSize: '18px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#1a1a2e',
  },
  statusCard: {
    background: '#fff',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  statusContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  statusRow: {
    fontSize: '14px',
    color: '#374151',
  },
  actionCard: {
    background: '#fff',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  actionDescription: {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '16px',
  },
  excelInfo: {
    background: '#f9fafb',
    borderRadius: '6px',
    padding: '16px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  downloadBtn: {
    background: '#059669',
    color: '#fff',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    marginBottom: '12px',
    marginRight: '12px',
    transition: 'all 0.2s',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  },
  fileInput: {
    marginBottom: '12px',
    padding: '8px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
  },
  fileSelected: {
    padding: '8px 12px',
    background: '#eff6ff',
    borderRadius: '6px',
    marginBottom: '12px',
    fontSize: '14px',
  },
  resultsCard: {
    background: '#fff',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  guideCard: {
    background: '#fff',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  guideDescription: {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '12px',
  },
  codeBlock: {
    background: '#1f2937',
    borderRadius: '6px',
    padding: '16px',
    overflow: 'auto',
  },
  button: {
    background: '#4f46e5',
    color: '#fff',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  buttonDisabled: {
    background: '#9ca3af',
    color: '#fff',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'not-allowed',
  },
  error: {
    background: '#fef2f2',
    color: '#dc2626',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    marginTop: '16px',
    padding: '20px',
    background: '#f3f4f6',
    borderRadius: '6px',
  },
  spinner: {
    width: '32px',
    height: '32px',
    border: '3px solid #e5e7eb',
    borderTopColor: '#4f46e5',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '12px',
  },
  summary: {
    display: 'flex',
    gap: '24px',
    marginBottom: '20px',
    padding: '16px',
    background: '#f9fafb',
    borderRadius: '6px',
  },
  summaryItem: {
    display: 'flex',
    flexDirection: 'column',
  },
  summaryLabel: {
    fontSize: '12px',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  summaryValue: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#1a1a2e',
  },
  resultsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  recommendation: {
    padding: '12px',
    background: '#fef3c7',
    borderRadius: '6px',
    fontSize: '14px',
    color: '#92400e',
  },
};

function getStatusStyle(status) {
  return {
    fontSize: '14px',
    color: status ? '#16a34a' : '#dc2626',
    padding: '8px',
    background: status ? '#f0fdf4' : '#fef2f2',
    borderRadius: '4px',
  };
}

function getResultStyle(status) {
  const base = {
    padding: '12px',
    borderRadius: '6px',
    border: '1px solid',
  };
  switch (status) {
    case 'success':
      return {...base, borderColor: '#16a34a', background: '#f0fdf4'};
    case 'failed':
      return {...base, borderColor: '#dc2626', background: '#fef2f2'};
    case 'no_image':
      return {...base, borderColor: '#6b7280', background: '#f9fafb'};
    default:
      return base;
  }
}

function getResultBadgeStyle(status) {
  const base = {
    fontSize: '12px',
    fontWeight: '600',
    padding: '4px 8px',
    borderRadius: '4px',
  };
  switch (status) {
    case 'success':
      return {...base, background: '#16a34a', color: '#fff'};
    case 'failed':
      return {...base, background: '#dc2626', color: '#fff'};
    case 'no_image':
      return {...base, background: '#6b7280', color: '#fff'};
    default:
      return base;
  }
}

export default Generate3DModelsPage;
