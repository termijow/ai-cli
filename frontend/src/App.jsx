import { useState, useEffect } from 'react';
import { 
  FileText, 
  MessageSquare, 
  FileSpreadsheet, 
  Languages, 
  Search, 
  Settings as SettingsIcon, 
  Moon, 
  Sun, 
  Cpu, 
  Activity, 
  ShieldCheck, 
  Zap 
} from 'lucide-react';

import DocumentEditor from './components/DocumentEditor';
import WhatsAppAnalyzer from './components/WhatsAppAnalyzer';
import SummaryTool from './components/SummaryTool';
import TranslateTool from './components/TranslateTool';
import ExtractTool from './components/ExtractTool';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState('documents');
  const [theme, setTheme] = useState(() => localStorage.getItem('ai_cli_theme') || 'dark');
  const [serverStatus, setServerStatus] = useState({ backend: false, llm: false, model: 'Qwen3.5' });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ai_cli_theme', theme);
  }, [theme]);

  // Check health periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:3094/health');
        if (res.ok) {
          const data = await res.json();
          setServerStatus({
            backend: true,
            llm: true,
            model: 'Qwen 3.5 (Local ROCm)'
          });
        } else {
          setServerStatus(prev => ({ ...prev, backend: false }));
        }
      } catch (e) {
        setServerStatus({ backend: false, llm: false, model: 'Offline' });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const tabs = [
    { id: 'documents', label: 'Editor & Docs', icon: FileText, desc: 'Editor y asistente contextual de IA' },
    { id: 'whatsapp', label: 'WhatsApp Analyzer', icon: MessageSquare, desc: 'Extracción de perfiles e inteligencia' },
    { id: 'summary', label: 'Resumir', icon: FileSpreadsheet, desc: 'Síntesis ejecutiva y puntos clave' },
    { id: 'translate', label: 'Traducir', icon: Languages, desc: 'Traducción local multilingüe' },
    { id: 'extract', label: 'Extraer Datos', icon: Search, desc: 'Entidades, fechas y métricas JSON' },
    { id: 'settings', label: 'Sistema', icon: SettingsIcon, desc: 'Estado de hardware y parámetros' },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-primary)' }}>
      {/* Top Header Bar */}
      <header style={{
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '12px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backdropFilter: 'blur(12px)'
      }}>
        {/* Brand & Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(16, 185, 129, 0.4)',
            color: '#fff'
          }}>
            <Zap size={22} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ margin: 0, fontSize: '17px', fontWeight: '800', letterSpacing: '-0.4px', color: 'var(--text-primary)' }}>
                AI-CLI STUDIO
              </h1>
              <span className="badge badge-emerald">PRO</span>
            </div>
            <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)' }}>
              Inteligencia Artificial Local Privada &bull; AMD ROCm
            </p>
          </div>
        </div>

        {/* Hardware Status Pills & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* LLM Status Pill */}
          <div style={{
            backgroundColor: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px'
          }}>
            <span className="live-dot" style={{ backgroundColor: serverStatus.backend ? '#10b981' : '#f43f5e', boxShadow: serverStatus.backend ? '0 0 8px #10b981' : 'none' }} />
            <Cpu size={14} style={{ color: 'var(--text-muted)' }} />
            <span style={{ color: 'var(--text-primary)', fontWeight: '600' }}>
              {serverStatus.backend ? serverStatus.model : 'Servidores Detenidos'}
            </span>
          </div>

          {/* Privacy badge */}
          <div style={{
            backgroundColor: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            color: 'var(--text-secondary)'
          }}>
            <ShieldCheck size={14} style={{ color: '#10b981' }} />
            <span>100% Offline</span>
          </div>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            title={`Cambiar a modo ${theme === 'dark' ? 'claro' : 'oscuro'}`}
            style={{
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {theme === 'dark' ? <Sun size={17} style={{ color: '#fbbf24' }} /> : <Moon size={17} />}
          </button>
        </div>
      </header>

      {/* Main Navigation Segmented Bar */}
      <nav style={{
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '4px 28px'
      }}>
        <div style={{
          display: 'flex',
          gap: '6px',
          maxWidth: '1280px',
          margin: '0 auto',
          overflowX: 'auto',
          padding: '4px 0'
        }}>
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '10px 18px',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
                  color: isActive ? '#10b981' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: isActive ? '700' : '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap',
                  boxShadow: isActive ? 'inset 0 0 0 1px var(--border-card)' : 'none'
                }}
              >
                <Icon size={16} style={{ color: isActive ? '#10b981' : 'var(--text-muted)' }} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Viewport Area */}
      <main style={{
        flex: 1,
        padding: '24px 28px',
        maxWidth: '1320px',
        width: '100%',
        margin: '0 auto',
        boxSizing: 'border-box'
      }}>
        <div className="animate-fade-in" key={activeTab}>
          {activeTab === 'documents' && <DocumentEditor />}
          {activeTab === 'whatsapp' && <WhatsAppAnalyzer />}
          {activeTab === 'summary' && <SummaryTool />}
          {activeTab === 'translate' && <TranslateTool />}
          {activeTab === 'extract' && <ExtractTool />}
          {activeTab === 'settings' && <Settings />}
        </div>
      </main>

      {/* Footer Status Line */}
      <footer style={{
        backgroundColor: 'var(--bg-secondary)',
        borderTop: '1px solid var(--border-subtle)',
        padding: '10px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span>AI-CLI Document & Intelligence Suite v2.0</span>
          <span>&bull;</span>
          <span>FastAPI :3094</span>
          <span>&bull;</span>
          <span>llama-server :1234</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={13} style={{ color: '#10b981' }} />
          <span>Local Engine Ready</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
