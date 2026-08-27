import { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Upload, 
  Download, 
  Zap, 
  Clock, 
  User, 
  Calendar, 
  MapPin, 
  Briefcase, 
  Heart, 
  Sparkles, 
  Layers, 
  FileText, 
  Check, 
  FolderArchive, 
  ArrowRight,
  TrendingUp,
  Cpu,
  Search,
  Eye,
  ShieldCheck,
  Terminal,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import MarkdownView from './MarkdownView';

function WhatsAppAnalyzer() {
  const backendUrl = 'http://localhost:3094';

  // Sync Status & Inventory
  const [syncStatus, setSyncStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedContactName, setSelectedContactName] = useState(null);
  const [selectedObsidianNote, setSelectedObsidianNote] = useState(null);
  const [loadingContactNote, setLoadingContactNote] = useState(false);

  // Center View: 'obsidian' | 'chat' | 'analyzer' | 'logs'
  const [centerView, setCenterView] = useState('obsidian');

  // Real-time Streaming Logs for Bulk Export
  const [liveLogs, setLiveLogs] = useState([]);
  const [isExportStreaming, setIsExportStreaming] = useState(false);
  const [batchLimit, setBatchLimit] = useState(100);
  const logsEndRef = useRef(null);

  // Chat Text & Analysis state
  const [chatText, setChatText] = useState('');
  const [fileName, setFileName] = useState('');
  const [stats, setStats] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progressInfo, setProgressInfo] = useState({ percent: 0, message: '', currentBatch: 0, totalBatches: 0, dateRange: '', tokens: 0 });
  const [error, setError] = useState(null);

  // Obsidian Vault Global Sync
  const [syncingObsidian, setSyncingObsidian] = useState(false);
  const [obsidianStatusMsg, setObsidianStatusMsg] = useState('');

  const loadSyncStatus = async () => {
    try {
      setLoadingStatus(true);
      const res = await fetch(`${backendUrl}/whatsapp/sync-status`);
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(data);
        if (!selectedContactName) {
          const first = data.chats?.[0]?.contact || data.obsidian_contacts?.[0]?.name;
          if (first) {
            handleSelectContact(first);
          }
        }
      }
    } catch (e) {
      console.error('Error loading sync status', e);
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    loadSyncStatus();
  }, []);

  useEffect(() => {
    if (centerView === 'logs' && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [liveLogs, centerView]);

  const handleSelectContact = async (name) => {
    if (!name) return;
    setSelectedContactName(name);
    setLoadingContactNote(true);
    setError(null);

    try {
      // 1. Fetch Obsidian note
      const res = await fetch(`${backendUrl}/whatsapp/obsidian-contact/${encodeURIComponent(name)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedObsidianNote(data);
      } else {
        setSelectedObsidianNote(null);
      }

      // 2. Fetch exported chat text
      const chatItem = syncStatus?.chats?.find(c => c.contact.toLowerCase() === name.toLowerCase());
      if (chatItem) {
        setFileName(chatItem.filename);
        const cRes = await fetch(`${backendUrl}/whatsapp/chats/${encodeURIComponent(chatItem.filename)}`);
        if (cRes.ok) {
          const cData = await cRes.json();
          setChatText(cData.content || '');
          setStats(null);
          setAnalysis(null);
        }
      } else {
        setFileName('');
        setChatText('');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingContactNote(false);
    }
  };

  const handleStartExportStream = async () => {
    setIsExportStreaming(true);
    setCenterView('logs');
    setLiveLogs([
      { time: new Date().toLocaleTimeString(), type: 'info', message: `🚀 Iniciando exportación automática (Meta: hasta ${batchLimit} chats)...` }
    ]);

    try {
      const response = await fetch(`${backendUrl}/whatsapp/export-all-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: Number(batchLimit) || 100, scrolls: 8 })
      });

      if (!response.ok) {
        throw new Error(`Error en el servidor: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.substring(6));
              setLiveLogs(prev => [
                ...prev,
                { time: new Date().toLocaleTimeString(), ...event }
              ]);

              if (event.type === 'done') {
                loadSyncStatus();
              }
            } catch (err) {}
          }
        }
      }
    } catch (err) {
      setLiveLogs(prev => [
        ...prev,
        { time: new Date().toLocaleTimeString(), type: 'error', message: `❌ Error: ${err.message}` }
      ]);
    } finally {
      setIsExportStreaming(false);
      loadSyncStatus();
    }
  };

  const handleExportObsidian = async () => {
    setSyncingObsidian(true);
    setObsidianStatusMsg('Sincronizando libreta Obsidian...');
    try {
      const res = await fetch(`${backendUrl}/whatsapp/export-obsidian`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        setObsidianStatusMsg(`✓ ${data.message || 'Libreta Obsidian actualizada con éxito'}`);
        loadSyncStatus();
      } else {
        const err = await res.json();
        setObsidianStatusMsg(`⚠️ ${err.detail || 'Error al exportar a Obsidian'}`);
      }
    } catch (e) {
      setObsidianStatusMsg(`⚠️ Error: ${e.message}`);
    } finally {
      setSyncingObsidian(false);
      setTimeout(() => setObsidianStatusMsg(''), 5000);
    }
  };

  const handleStreamAnalysis = async () => {
    if (!chatText.trim()) return;

    setLoading(true);
    setError(null);
    setCenterView('analyzer');
    setProgressInfo({ percent: 5, message: 'Iniciando particionado con Qwen 3.6...', currentBatch: 0, totalBatches: 0, dateRange: '', tokens: 0 });

    try {
      const response = await fetch(`${backendUrl}/whatsapp/analyze-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_text: chatText })
      });

      if (!response.ok) {
        throw new Error(`Error en el servidor: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.substring(6));

              if (event.type === 'init') {
                setStats(event.stats);
                setProgressInfo(prev => ({
                  ...prev,
                  totalBatches: event.total_chunks,
                  percent: 10,
                  message: `Detectados ${event.total_messages.toLocaleString()} mensajes. Procesando en ${event.total_chunks} fragmentos...`
                }));
              } else if (event.type === 'batch_start') {
                setProgressInfo(prev => ({
                  ...prev,
                  percent: event.percent,
                  currentBatch: event.batch_index,
                  totalBatches: event.total_batches,
                  dateRange: event.date_range,
                  message: event.message
                }));
              } else if (event.type === 'batch_complete') {
                setProgressInfo(prev => ({
                  ...prev,
                  percent: event.percent,
                  currentBatch: event.batch_index,
                  tokens: event.total_tokens
                }));
                if (event.current_profile) {
                  setAnalysis(event.current_profile);
                }
              } else if (event.type === 'complete') {
                setProgressInfo(prev => ({
                  ...prev,
                  percent: 100,
                  message: '✓ ¡Análisis por batches completado con éxito!'
                }));
                setAnalysis(event.profile);
                loadSyncStatus();
                if (selectedContactName) {
                  handleSelectContact(selectedContactName);
                }
              } else if (event.type === 'error') {
                setError(event.message);
              }
            } catch (err) {}
          }
        }
      }
    } catch (err) {
      setError(`Error durante el análisis: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Contacts List computation for the Aside
  const contactsList = (() => {
    const map = new Map();

    if (syncStatus?.obsidian_contacts) {
      for (const oc of syncStatus.obsidian_contacts) {
        map.set(oc.name.toLowerCase(), {
          name: oc.name,
          hasObsidian: true,
          isExported: false,
          chatFilename: null,
          size_kb: null,
          cumpleanos: oc.cumpleanos,
          ubicacion: oc.ubicacion,
          profesion: oc.profesion,
          modified: oc.modified
        });
      }
    }

    if (syncStatus?.chats) {
      for (const ch of syncStatus.chats) {
        const key = ch.contact.toLowerCase();
        const existing = map.get(key);
        if (existing) {
          existing.isExported = true;
          existing.chatFilename = ch.filename;
          existing.size_kb = ch.size_kb;
          if (ch.modified > (existing.modified || 0)) {
            existing.modified = ch.modified;
          }
        } else {
          map.set(key, {
            name: ch.contact,
            hasObsidian: ch.has_obsidian,
            isExported: true,
            chatFilename: ch.filename,
            size_kb: ch.size_kb,
            cumpleanos: ch.obsidian_info?.cumpleanos,
            ubicacion: ch.obsidian_info?.ubicacion,
            profesion: ch.obsidian_info?.profesion,
            modified: ch.modified
          });
        }
      }
    }

    const arr = Array.from(map.values());
    if (!searchQuery.trim()) return arr;
    const q = searchQuery.toLowerCase();
    return arr.filter(c => 
      c.name.toLowerCase().includes(q) || 
      (c.ubicacion && c.ubicacion.toLowerCase().includes(q)) || 
      (c.profesion && c.profesion.toLowerCase().includes(q))
    );
  })();

  const currentContactData = contactsList.find(c => c.name.toLowerCase() === (selectedContactName || '').toLowerCase());

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Top Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <MessageSquare size={24} style={{ color: '#10b981' }} />
            WhatsApp Intelligence & Obsidian CRM Studio
          </h2>
          <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
            Extracción masiva y memoria incremental en tu libreta Obsidian (~/Documents/Obsidian_WhatsApp_CRM).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          {obsidianStatusMsg && (
            <span style={{ fontSize: '12px', color: '#10b981', fontWeight: '600' }}>
              {obsidianStatusMsg}
            </span>
          )}

          <button
            onClick={handleExportObsidian}
            disabled={syncingObsidian}
            className="btn-secondary"
            title="Sincronizar base de datos de Obsidian CRM"
            style={{ fontSize: '13px', padding: '8px 14px', backgroundColor: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.4)', color: '#a5b4fc' }}
          >
            <Sparkles size={14} style={{ color: '#818cf8' }} />
            <span>{syncingObsidian ? 'Sincronizando...' : '🔮 Actualizar Bóveda Obsidian'}</span>
          </button>

          <button
            onClick={loadSyncStatus}
            disabled={loadingStatus}
            className="btn-secondary"
            style={{ fontSize: '13px', padding: '8px 12px' }}
            title="Refrescar estado"
          >
            <RefreshCw size={14} className={loadingStatus ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Main Studio Grid: ASIDE (Left) + MAIN WORKSPACE (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '18px', alignItems: 'start' }}>
        
        {/* ASIDE: Chats & Contacts Directory */}
        <aside className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', height: 'calc(100vh - 160px)', position: 'sticky', top: '20px' }}>
          
          {/* Header & Badges */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <strong style={{ fontSize: '14px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={16} style={{ color: '#10b981' }} />
                Directorio de Contactos
              </strong>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {contactsList.length} en lista
              </span>
            </div>

            <div style={{ display: 'flex', gap: '6px', fontSize: '11px', flexWrap: 'wrap' }}>
              <span className="badge badge-emerald" title="Chats exportados a .txt">
                ✓ Exportados: {syncStatus?.total_exported || 0}
              </span>
              <span className="badge badge-indigo" title="Perfiles en libreta Obsidian">
                📓 Obsidian: {syncStatus?.total_obsidian_contacts || 0}
              </span>
            </div>
          </div>

          {/* Quick Action Button: Bulk Sync */}
          <div style={{ padding: '10px', backgroundColor: 'rgba(16, 185, 129, 0.08)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16, 185, 129, 0.25)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)' }}>
                ⚡ Exportar WhatsApp Web
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Lím:</span>
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={batchLimit}
                  onChange={(e) => setBatchLimit(e.target.value)}
                  style={{
                    width: '45px',
                    padding: '2px 4px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-input)',
                    color: 'var(--text-primary)',
                    fontSize: '11px'
                  }}
                />
              </div>
            </div>

            <button
              onClick={handleStartExportStream}
              disabled={isExportStreaming}
              className="btn-primary"
              style={{
                fontSize: '12px',
                padding: '6px 12px',
                backgroundColor: '#10b981',
                borderColor: '#10b981',
                width: '100%',
                justifyContent: 'center'
              }}
            >
              {isExportStreaming ? (
                <>
                  <RefreshCw size={13} className="animate-spin" />
                  <span>Sincronizando en vivo...</span>
                </>
              ) : (
                <>
                  <Zap size={13} />
                  <span>🚀 Sincronizar Faltantes</span>
                </>
              )}
            </button>
          </div>

          {/* Search Box */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Buscar contacto o chat..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px 8px 30px',
                fontSize: '12px',
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Scrollable Contacts List */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '2px' }}>
            {contactsList.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--text-muted)', fontSize: '13px' }}>
                {searchQuery ? 'No hay contactos que coincidan.' : 'No hay chats exportados aún.'}
              </div>
            ) : (
              contactsList.map((contact) => {
                const isSelected = selectedContactName?.toLowerCase() === contact.name.toLowerCase();
                return (
                  <div
                    key={contact.name}
                    onClick={() => handleSelectContact(contact.name)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'var(--bg-input)',
                      border: isSelected ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      backgroundColor: isSelected ? '#10b981' : 'rgba(255, 255, 255, 0.08)',
                      color: isSelected ? '#ffffff' : 'var(--text-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      fontSize: '13px',
                      flexShrink: 0
                    }}>
                      {contact.name.charAt(0).toUpperCase()}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {contact.name}
                        </span>
                      </div>

                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: '2px' }}>
                        {contact.profesion || contact.ubicacion || (contact.isExported ? `${contact.size_kb} KB exportados` : 'En Obsidian')}
                      </div>

                      <div style={{ display: 'flex', gap: '4px', marginTop: '4px', flexWrap: 'wrap' }}>
                        {contact.isExported && (
                          <span style={{ fontSize: '10px', color: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.15)', padding: '1px 5px', borderRadius: '4px' }}>
                            ✓ Chat
                          </span>
                        )}
                        {contact.hasObsidian && (
                          <span style={{ fontSize: '10px', color: '#a5b4fc', backgroundColor: 'rgba(99, 102, 241, 0.15)', padding: '1px 5px', borderRadius: '4px' }}>
                            📓 CRM
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span>🔒 Modo Seguro: omite automáticamente chats sin leer.</span>
          </div>
        </aside>

        {/* MAIN WORKSPACE */}
        <main style={{ display: 'flex', flexDirection: 'column', gap: '16px', minWidth: 0 }}>
          
          {/* Active Contact Header & Tabs */}
          <div className="glass-panel" style={{ padding: '18px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                color: '#10b981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '800',
                fontSize: '18px'
              }}>
                {selectedContactName ? selectedContactName.charAt(0).toUpperCase() : '?'}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {selectedContactName || 'Selecciona un contacto'}
                </h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {fileName ? `Archivo: ${fileName}` : 'Sin archivo de chat cargado'}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '6px', backgroundColor: 'var(--bg-input)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', flexWrap: 'wrap' }}>
              <button
                onClick={() => setCenterView('obsidian')}
                className={centerView === 'obsidian' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                <BookOpen size={13} />
                <span>📓 Libreta Obsidian</span>
              </button>

              <button
                onClick={() => setCenterView('chat')}
                className={centerView === 'chat' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                <MessageSquare size={13} />
                <span>💬 Transcripción</span>
              </button>

              <button
                onClick={() => setCenterView('analyzer')}
                className={centerView === 'analyzer' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                <Cpu size={13} />
                <span>⚡ Analizar</span>
              </button>

              <button
                onClick={() => setCenterView('logs')}
                className={centerView === 'logs' ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '12px', padding: '6px 12px', position: 'relative' }}
              >
                <Terminal size={13} />
                <span>📺 Consola en Vivo</span>
                {isExportStreaming && (
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981', position: 'absolute', top: '6px', right: '6px' }} />
                )}
              </button>
            </div>
          </div>

          {/* VIEW 1: OBSIDIAN CRM NOTE */}
          {centerView === 'obsidian' && (
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {currentContactData && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                      <Calendar size={13} style={{ color: '#f59e0b' }} />
                      <span>Cumpleaños</span>
                    </div>
                    <strong style={{ display: 'block', marginTop: '4px', fontSize: '13px', color: 'var(--text-primary)' }}>
                      {currentContactData.cumpleanos || 'No registrado aún'}
                    </strong>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                      <MapPin size={13} style={{ color: '#f43f5e' }} />
                      <span>Ubicación / Dirección</span>
                    </div>
                    <strong style={{ display: 'block', marginTop: '4px', fontSize: '13px', color: 'var(--text-primary)' }}>
                      {currentContactData.ubicacion || 'No registrada aún'}
                    </strong>
                  </div>

                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                      <Briefcase size={13} style={{ color: '#6366f1' }} />
                      <span>Profesión / Trabajo</span>
                    </div>
                    <strong style={{ display: 'block', marginTop: '4px', fontSize: '13px', color: 'var(--text-primary)' }}>
                      {currentContactData.profesion || 'No registrada aún'}
                    </strong>
                  </div>
                </div>
              )}

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={16} style={{ color: '#818cf8' }} />
                    <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                      Nota Markdown en Obsidian CRM (~/Documents/Obsidian_WhatsApp_CRM)
                    </strong>
                  </div>

                  {selectedObsidianNote && (
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {selectedObsidianNote.filename}
                    </span>
                  )}
                </div>

                {loadingContactNote ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 10px' }} />
                    <span>Cargando nota desde Obsidian...</span>
                  </div>
                ) : selectedObsidianNote?.content ? (
                  <div style={{ backgroundColor: 'var(--bg-input)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <MarkdownView content={selectedObsidianNote.content} />
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', backgroundColor: 'var(--bg-input)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-subtle)' }}>
                    <AlertCircle size={28} style={{ color: '#f59e0b', margin: '0 auto 10px' }} />
                    <h4 style={{ margin: '0 0 6px', color: 'var(--text-primary)' }}>
                      Aún no hay ficha de Obsidian para {selectedContactName}
                    </h4>
                    <p style={{ margin: '0 0 16px', color: 'var(--text-muted)', fontSize: '13px' }}>
                      Pasa a la pestaña <strong>"⚡ Analizar"</strong> para procesar los mensajes y generar su ficha de inteligencia automáticamente.
                    </p>
                    <button
                      onClick={() => setCenterView('analyzer')}
                      className="btn-primary"
                      style={{ fontSize: '13px', padding: '8px 16px' }}
                    >
                      <Cpu size={14} />
                      <span>Ir a Analizar Conversación</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* VIEW 2: CHAT TRANSCRIPT */}
          {centerView === 'chat' && (
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <strong style={{ fontSize: '15px', color: 'var(--text-primary)' }}>
                    Conversación de WhatsApp con {selectedContactName || 'Contacto'}
                  </strong>
                    {chatText ? `${chatText.split('\n').length.toLocaleString()} líneas cargadas` : 'Sin mensajes'}
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => {
                      const blob = new Blob([chatText], { type: 'text/plain;charset=utf-8' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = fileName || `Chat_${selectedContactName}.txt`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    disabled={!chatText}
                    className="btn-secondary"
                    style={{ fontSize: '12px' }}
                  >
                    <Download size={13} />
                    <span>Descargar .txt</span>
                  </button>

                  <button
                    onClick={() => { setCenterView('analyzer'); handleStreamAnalysis(); }}
                    disabled={!chatText || loading}
                    className="btn-primary"
                    style={{ fontSize: '12px', backgroundColor: '#10b981', borderColor: '#10b981' }}
                  >
                    <Cpu size={13} />
                    <span>Analizar con Qwen 3.6</span>
                  </button>
                </div>
              </div>

              <textarea
                value={chatText}
                onChange={(e) => setChatText(e.target.value)}
                placeholder="No hay conversación seleccionada o el archivo está vacío..."
                style={{
                  width: '100%',
                  height: '420px',
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  fontSize: '13px',
                  fontFamily: 'var(--font-mono)',
                  resize: 'vertical',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          )}

          {/* VIEW 3: QWEN 3.6 ANALYZER */}
          {centerView === 'analyzer' && (
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '17px', fontWeight: '800', color: 'var(--text-primary)' }}>
                    🧠 Extractor por Batches con Qwen 3.6 35B A3B
                  </h3>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Procesa la conversación en fragmentos con contexto de 40k para extraer hechos, direcciones y eventos sin límites de tokens.
                  </p>
                </div>

                <button
                  onClick={handleStreamAnalysis}
                  disabled={loading || !chatText.trim()}
                  className="btn-primary"
                  style={{ fontSize: '13px', padding: '8px 18px', backgroundColor: '#10b981', borderColor: '#10b981' }}
                >
                  <Cpu size={14} />
                  <span>{loading ? 'Procesando Batches...' : '🚀 Iniciar Análisis'}</span>
                </button>
              </div>

              {loading && (
                <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '8px' }}>
                    <span style={{ color: '#10b981', fontWeight: '700' }}>{progressInfo.message}</span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: '700' }}>{progressInfo.percent}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-input)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${progressInfo.percent}%`, height: '100%', backgroundColor: '#10b981', transition: 'width 0.3s ease' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                    <span>Fragmento: {progressInfo.currentBatch} / {progressInfo.totalBatches}</span>
                    <span>Tokens procesados: {progressInfo.tokens.toLocaleString()}</span>
                  </div>
                </div>
              )}

              {analysis && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
                    <strong style={{ fontSize: '15px', color: 'var(--text-primary)' }}>
                      ✨ Perfil de Inteligencia Extraído
                    </strong>
                    <span className="badge badge-emerald">Guardado en Obsidian CRM</span>
                  </div>

                  {analysis.participantes?.map((p, idx) => (
                    <div key={idx} style={{ backgroundColor: 'var(--bg-tertiary)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)' }}>
                      <h4 style={{ margin: '0 0 10px', fontSize: '16px', color: 'var(--text-primary)' }}>👤 {p.nombre}</h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                        <div><strong>🎂 Cumpleaños:</strong> {p.cumpleanos || 'No mencionado'}</div>
                        <div><strong>📍 Ubicación:</strong> {p.direccion_ubicacion || 'No mencionada'}</div>
                        <div><strong>💼 Profesión:</strong> {p.profesion_ocupacion || 'No mencionada'}</div>
                      </div>

                      {p.notas_clave?.length > 0 && (
                        <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                          <strong style={{ fontSize: '12px', color: 'var(--text-primary)' }}>📝 Hechos y Anécdotas Guardadas:</strong>
                          <ul style={{ margin: '6px 0 0', paddingLeft: '20px', fontSize: '12px' }}>
                            {p.notas_clave.map((n, i) => (
                              <li key={i}>{n}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* VIEW 4: LIVE TERMINAL CONSOLE */}
          {centerView === 'logs' && (
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={18} style={{ color: '#10b981' }} />
                  <strong style={{ fontSize: '15px', color: 'var(--text-primary)' }}>
                    Consola en Vivo — Exportador Inteligente de WhatsApp Web
                  </strong>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {isExportStreaming ? (
                    <span style={{ fontSize: '12px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981', animation: 'pulse 1.5s infinite' }} />
                      Navegador en ejecución...
                    </span>
                  ) : (
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Inactivo
                    </span>
                  )}

                  <button
                    onClick={() => setLiveLogs([])}
                    className="btn-secondary"
                    style={{ fontSize: '11px', padding: '4px 8px' }}
                  >
                    Limpiar
                  </button>
                </div>
              </div>

              <div style={{
                backgroundColor: '#090d16',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                lineHeight: '1.6',
                height: '420px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px'
              }}>
                {liveLogs.length === 0 ? (
                  <div style={{ color: '#64748b', textAlign: 'center', marginTop: '160px' }}>
                    Aquí verás el registro en tiempo real de WhatsApp Web.<br/>
                    Presiona <strong>"🚀 Sincronizar Faltantes"</strong> en la barra lateral para comenzar.
                  </div>
                ) : (
                  liveLogs.map((log, idx) => {
                    let color = '#94a3b8';
                    if (log.type === 'skip_cached') color = '#38bdf8';
                    if (log.type === 'skip_unread') color = '#f59e0b';
                    if (log.type === 'exported') color = '#10b981';
                    if (log.type === 'error') color = '#f43f5e';
                    if (log.type === 'done') color = '#a78bfa';

                    return (
                      <div key={idx} style={{ color }}>
                        <span style={{ color: '#475569', marginRight: '8px' }}>[{log.time}]</span>
                        <span>{log.message}</span>
                      </div>
                    );
                  })
                )}
                <div ref={logsEndRef} />
              </div>

              <div style={{ padding: '12px', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={18} style={{ color: '#10b981', flexShrink: 0 }} />
                <span>
                  <strong>Protección de Privacidad:</strong> El exportador detecta chats con mensajes sin leer y los omite automáticamente para no marcarlos como leídos en tu teléfono. Tampoco re-descarga chats que ya existen en tu equipo.
                </span>
              </div>
            </div>
          )}

        </main>
      </div>

    </div>
  );
}

export default WhatsAppAnalyzer;
