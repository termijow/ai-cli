import { useState } from 'react';
import DocumentEditor from './components/DocumentEditor';
import SummaryTool from './components/SummaryTool';
import TranslateTool from './components/TranslateTool';
import ExtractTool from './components/ExtractTool';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState('documents');

  const tabs = [
    { id: 'documents', label: 'Documentos', icon: '📄' },
    { id: 'summary', label: 'Resumir', icon: '📊' },
    { id: 'translate', label: 'Traducir', icon: '🌐' },
    { id: 'extract', label: 'Extraer', icon: '🔍' },
    { id: 'settings', label: 'Configuración', icon: '⚙️' },
  ];

  return (
    <div style={{ minHeight: '100vh', fontFamily: 'system-ui, sans-serif', backgroundColor: '#f5f5f5' }}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Header */}
        <header style={{ backgroundColor: '#217346', color: 'white', padding: '20px 30px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h1 style={{ margin: 0, fontSize: '28px' }}>AI-CLI</h1>
          <p style={{ margin: '8px 0 0 0', opacity: 0.9 }}>Servicios de Inteligencia Artificial</p>
        </header>

        {/* Navigation Tabs */}
        <nav style={{ backgroundColor: '#fff', borderBottom: '1px solid #ddd' }}>
          <div style={{ display: 'flex', maxWidth: '1200px', margin: '0 auto', padding: '0 20px' }}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '15px 25px',
                  border: 'none',
                  backgroundColor: activeTab === tab.id ? '#217346' : '#f5f5f5',
                  color: activeTab === tab.id ? 'white' : '#333',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: activeTab === tab.id ? '600' : '400',
                  transition: 'background-color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </nav>

        {/* Main Content */}
        <main style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
          {activeTab === 'documents' && <DocumentEditor />}
          {activeTab === 'summary' && <SummaryTool />}
          {activeTab === 'translate' && <TranslateTool />}
          {activeTab === 'extract' && <ExtractTool />}
          {activeTab === 'settings' && <Settings />}
        </main>

        {/* Footer */}
        <footer style={{ 
          backgroundColor: '#fff', 
          borderTop: '1px solid #ddd', 
          padding: '15px 30px',
          textAlign: 'center',
          fontSize: '12px',
          color: '#666'
        }}>
          <p>AI-CLI Backend v0.1 | Backend: http://localhost:3094 | Backend AI: http://localhost:1234</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
