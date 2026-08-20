import { useState, useRef } from 'react';

function SummaryTool() {
  const [selectedFile, setSelectedFile] = useState('');
  const [summaryOptions, setSummaryOptions] = useState({
    length: 'medium',
    format: 'text'
  });
  const [summaryResult, setSummaryResult] = useState('');
  const [loading, setLoading] = useState(false);

  const backendUrl = 'http://localhost:3094';

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.value);
  };

  const handleSummary = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/documents/${selectedFile}/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          length: summaryOptions.length,
          format: summaryOptions.format
        })
      });

      const data = await response.json();
      setSummaryResult(data.summary || data.result || '');
    } catch (error) {
      setSummaryResult('Error al procesar el documento. Asegúrate de que el backend esté en http://localhost:3094');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2 style={{ fontSize: '24px', color: '#333', marginBottom: '20px' }}>Resumir Documento</h2>

      {/* File Selection */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
          Selecciona un documento para resumir
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

      {/* Options */}
      <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '15px', color: '#666', fontSize: '13px' }}>
          Opciones de resumen
        </label>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', color: '#333', fontSize: '13px' }}>
              Longitud
            </label>
            <select
              className="select"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '13px'
              }}
              value={summaryOptions.length}
              onChange={(e) => setSummaryOptions({ ...summaryOptions, length: e.target.value })}
            >
              <option value="short">Breve</option>
              <option value="medium">Medio</option>
              <option value="long">Detallado</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', color: '#333', fontSize: '13px' }}>
              Formato
            </label>
            <select
              className="select"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '13px'
              }}
              value={summaryOptions.format}
              onChange={(e) => setSummaryOptions({ ...summaryOptions, format: e.target.value })}
            >
              <option value="text">Texto</option>
              <option value="markdown">Markdown</option>
            </select>
          </div>
        </div>
      </div>

      {/* Button */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          className="btn btn-primary"
          onClick={handleSummary}
          disabled={!selectedFile || loading}
          style={{
            padding: '12px 30px',
            fontSize: '14px'
          }}
        >
          {loading ? '🔄 Procesando...' : '📊 Generar Resumen'}
        </button>
      </div>

      {/* Result */}
      {summaryResult && (
        <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <label style={{ display: 'block', marginBottom: '15px', color: '#666', fontSize: '13px' }}>
            Resumen generado
          </label>
          <div className="code" style={{ backgroundColor: '#f9f9f9', borderRadius: '4px', padding: '15px', border: '1px solid #eee', overflowX: 'auto' }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {summaryResult}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default SummaryTool;
