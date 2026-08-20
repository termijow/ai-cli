import { useState, useRef } from 'react';

function DocumentEditor() {
  const [files, setFiles] = useState([]);
  const [currentFile, setCurrentFile] = useState(null);
  const [currentContent, setCurrentContent] = useState('');
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const fileInputRef = useRef(null);

  const backendUrl = 'http://localhost:3094';

  const handleFiles = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const newFiles = selectedFiles.map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    setCurrentFile(newFiles[0].name);
    setCurrentContent('');
  };

  const selectFile = (file) => {
    setCurrentFile(file.name);
    const savedContent = localStorage.getItem(file.name) || '';
    setCurrentContent(savedContent);
  };

  const saveDocument = () => {
    if (currentFile) {
      localStorage.setItem(currentFile, currentContent);
      alert(`Documento "${currentFile}" guardado en localStorage`);
    }
  };

  const handleAiSubmit = async () => {
    if (!currentFile || !aiPrompt.trim()) return;
    
    setAiLoading(true);
    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: aiPrompt,
          file: currentFile
        })
      });
      
      const data = await response.json();
      setAiResponse(data.response || '');
    } catch (error) {
      setAiResponse('Error al conectar con el backend AI. Asegúrate de que esté en http://localhost:3094');
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%', backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
      {/* Sidebar */}
      <div style={{ width: '280px', borderRight: '1px solid #eee', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #eee' }}>
          <h3 style={{ margin: 0, fontSize: '16px', color: '#333' }}>Mis Documentos</h3>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
          <button
            className="btn btn-primary mb-2"
            style={{ width: '100%', marginBottom: '10px' }}
            onClick={() => fileInputRef.current?.click()}
          >
            📁 Abrir/Importar
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFiles}
            multiple
            accept=".doc,.docx,.txt,.md,.html,.json,.pdf"
            style={{ display: 'none' }}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {files.map(file => (
              <button
                key={file.id}
                className={`btn ${currentFile === file.name ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => selectFile(file.name)}
                style={{ 
                  textAlign: 'left', 
                  justifyContent: 'flex-start',
                  width: '100%',
                  padding: '10px',
                  fontSize: '13px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>📄</span>
                  <span>{file.name}</span>
                  <span style={{ 
                    marginLeft: 'auto', 
                    fontSize: '11px', 
                    opacity: 0.6 
                  }}>
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div style={{ padding: '15px', borderTop: '1px solid #eee', backgroundColor: '#fafafa' }}>
          <button
            className="btn btn-secondary"
            onClick={saveDocument}
            style={{ width: '100%' }}
          >
            💾 Guardar
          </button>
        </div>
      </div>

      {/* Main Editor Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Toolbar */}
        <div style={{ padding: '15px 20px', borderBottom: '1px solid #eee', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            className="select"
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '13px'
            }}
          >
            <option value="">Selecciona un documento...</option>
            {files.map(file => (
              <option key={file.id} value={file.name}>{file.name}</option>
            ))}
          </select>
          
          <button className="btn btn-secondary" onClick={() => setShowAIAssistant(!showAIAssistant)}>
            {showAIAssistant ? '❌' : '🤖'} Asistente AI
          </button>
        </div>

        {/* Editor Content */}
        <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
          <div style={{ backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', minHeight: '400px' }}>
            <textarea
              className="textarea"
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                padding: '20px',
                fontFamily: 'system-ui, sans-serif',
                fontSize: '14px',
                resize: 'none',
                outline: 'none',
                lineHeight: '1.6'
              }}
              value={currentContent}
              onChange={(e) => setCurrentContent(e.target.value)}
              placeholder={currentFile ? 'Edita tu documento aquí...' : 'Selecciona un documento para editar'}
            />
          </div>
        </div>

        {/* AI Assistant Modal */}
        {showAIAssistant && (
          <div style={{
            position: 'fixed',
            top: '70px',
            left: '280px',
            right: '20px',
            bottom: '100px',
            backgroundColor: '#fff',
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{ padding: '15px 20px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, color: '#333' }}>Asistente AI para {currentFile || 'documento'}</h4>
              <button
                className="btn btn-secondary"
                onClick={() => setShowAIAssistant(false)}
                style={{ padding: '5px 10px' }}
              >
                ✕
              </button>
            </div>

            <div style={{ flex: 1, padding: '15px 20px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <input
                  className="input"
                  style={{
                    flex: 1,
                    padding: '10px 12px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '13px'
                  }}
                  placeholder="Pide ayuda a la AI..."
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAiSubmit()}
                />
                <button
                  className="btn btn-primary"
                  onClick={handleAiSubmit}
                  disabled={aiLoading}
                >
                  {aiLoading ? '✋' : '➤'}
                </button>
              </div>

              {aiResponse && (
                <div style={{ marginTop: '15px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px', border: '1px solid #eee' }}>
                  <h5 style={{ margin: '0 0 10px 0', color: '#666', fontSize: '12px', textTransform: 'uppercase' }}>
                    AI Response
                  </h5>
                  <div style={{ color: '#333', lineHeight: '1.6' }}>
                    {aiResponse}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DocumentEditor;
