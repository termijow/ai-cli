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
  Zap,
  Lock,
  Key,
  LogOut,
  ArrowRight
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
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('ai_auth_token') || '');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ai_cli_theme', theme);
  }, [theme]);

  // Check health periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/health');
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

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    if (!loginPassword.trim()) return;
    setIsLoggingIn(true);
    setLoginError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: loginPassword })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.token) {
          localStorage.setItem('ai_auth_token', data.token);
          setAuthToken(data.token);
          setLoginPassword('');
        }
      } else {
        const err = await res.json().catch(() => ({ detail: 'Contraseña incorrecta' }));
        setLoginError(err.detail || 'Contraseña incorrecta.');
      }
    } catch (err) {
      setLoginError('No se pudo conectar con el servidor de autenticación.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('ai_auth_token');
    setAuthToken('');
  };

  const tabs = [
    { id: 'documents', label: 'Editor & Docs', icon: FileText, desc: 'Editor y asistente contextual de IA' },
    { id: 'whatsapp', label: 'WhatsApp Analyzer', icon: MessageSquare, desc: 'Extracción de perfiles e inteligencia' },
    { id: 'summary', label: 'Resumir', icon: FileSpreadsheet, desc: 'Síntesis ejecutiva y puntos clave' },
    { id: 'translate', label: 'Traducir', icon: Languages, desc: 'Traducción local multilingüe' },
    { id: 'extract', label: 'Extraer Datos', icon: Search, desc: 'Entidades, fechas y métricas JSON' },
    { id: 'settings', label: 'Sistema', icon: SettingsIcon, desc: 'Estado de hardware y parámetros' },
  ];

  // Auth Gate Screen
  if (!authToken) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-primary)',
        padding: '20px'
      }}>
        <div style={{
          maxWidth: '420px',
          width: '100%',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '16px',
          padding: '36px 32px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
          textAlign: 'center'
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            color: '#fff',
            boxShadow: '0 0 20px rgba(16, 185, 129, 0.4)'
          }}>
            <Lock size={28} />
          </div>

          <h2 style={{ margin: '0 0 8px', fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)' }}>
            AI-CLI Security Wall
          </h2>
          <p style={{ margin: '0 0 24px', fontSize: '13px', color: 'var(--text-muted)' }}>
            Acceso restringido a inteligencia y base de datos privada.
          </p>

          <form onSubmit={handleLogin}>
            <div style={{ position: 'relative', marginBottom: '16px' }}>
              <Key size={18} style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
              <input
                type="password"
                placeholder="Ingresa la Contraseña Maestra..."
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                autoFocus
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '12px 14px 12px 42px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: 'var(--bg-tertiary)',
                  color: 'var(--text-primary)',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
            </div>

            {loginError && (
              <div style={{
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                color: '#fb7185',
                padding: '8px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                marginBottom: '16px',
                textAlign: 'left'
              }}>
                {loginError}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoggingIn || !loginPassword.trim()}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: '#10b981',
                color: '#fff',
                fontWeight: '700',
                fontSize: '14px',
                cursor: isLoggingIn ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'background 0.2s',
                opacity: isLoggingIn || !loginPassword.trim() ? 0.6 : 1
              }}
            >
              <span>{isLoggingIn ? 'Verificando...' : 'Acceder al Sistema'}</span>
              <ArrowRight size={16} />
            </button>
          </form>
        </div>
      </div>
    );
  }

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

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            title="Cerrar Sesión"
            style={{
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
              color: '#fb7185',
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
            <LogOut size={16} />
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
