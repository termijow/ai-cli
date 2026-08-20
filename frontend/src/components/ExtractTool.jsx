import { useState } from 'react';

function ExtractTool() {
  const [selectedFile, setSelectedFile] = useState('');
  const [extractType, setExtractType] = useState('entities');
  const [extractResult, setExtractResult] = useState('');
  const [loading, setLoading] = useState(false);

  const backendUrl = 'http://localhost:3094';

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.value);
  };

  const handleExtract = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/documents/${selectedFile}/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          type: extractType
        })
      });

      const data = await response.json();
      setExtractResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setExtractResult('Error al extraer información. Asegúrate de que el backend esté en http://localhost:3094');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2 style={{ fontSize: '24px', color: '#333', marginBottom: '20px' }}>Extraer Información</h2>

      {/* File Selection */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
          Selecciona un documento para extraer
        </label>
        <select
          className="select"
          style={{
            width: '100%',
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }}
          value={selectedFile}
          onChange={handleFileSelect}
        >
          <option value="">-- Selecciona un documento --</option>
        </select>
      </div>

      {/* Extract Type */}
      <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '15px', color: '#666', fontSize: '13px' }}>
          Tipo de extracción
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
          {['entities', 'dates', 'numbers'].map(type => (
            <button
              key={type}
              className="btn btn-secondary"
              onClick={() => setExtractType(type)}
              style={{
                padding: '12px',
                fontSize: '13px',
                minWidth: '100%',
                backgroundColor: extractType === type ? '#5D79A4' : '#f5f5f5',
                color: extractType === type ? '#fff' : '#333',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Button */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          className="btn btn-primary"
          onClick={handleExtract}
          disabled={!selectedFile || loading}
          style={{
            padding: '12px 30px',
            fontSize: '14px'
          }}
        >
          {loading ? '🔄 Procesando...' : '🔍 Extraer Información'}
        </button>
      </div>

      {/* Result */}
      {extractResult && (
        <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
            Resultado de extracción
          </label>
          <div className="code" style={{ backgroundColor: '#f9f9f9', borderRadius: '4px', padding: '15px', border: '1px solid #eee', overflowX: 'auto', height: '400px', overflowY: 'auto' }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {extractResult}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExtractTool;
