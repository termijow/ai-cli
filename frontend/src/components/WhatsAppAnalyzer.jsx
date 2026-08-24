import { useState, useEffect } from 'react';
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
  Cpu
} from 'lucide-react';
import MarkdownView from './MarkdownView';

function WhatsAppAnalyzer() {
  const [chatText, setChatText] = useState('');
  const [activeSubTab, setActiveSubTab] = useState('analyzer'); // 'analyzer' | 'saved'
  const [stats, setStats] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progressInfo, setProgressInfo] = useState({ percent: 0, message: '', currentBatch: 0, totalBatches: 0, dateRange: '', tokens: 0 });
  const [savedDossiers, setSavedDossiers] = useState([]);
  const [selectedDossier, setSelectedDossier] = useState(null);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');

  const backendUrl = 'http://localhost:3094';

  const loadSavedDossiers = async () => {
    try {
      const res = await fetch(`${backendUrl}/whatsapp/dossiers`);
      if (res.ok) {
        const data = await res.json();
        setSavedDossiers(data.dossiers || []);
      }
    } catch (e) {}
  };

  useEffect(() => {
    loadSavedDossiers();
  }, []);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      setChatText(event.target.result || '');
      setStats(null);
      setAnalysis(null);
      setError(null);
      setProgressInfo({ percent: 0, message: '', currentBatch: 0, totalBatches: 0, dateRange: '', tokens: 0 });
    };
    reader.readAsText(file);
  };

  const handleStreamAnalysis = async () => {
    if (!chatText.trim()) return;

    setLoading(true);
    setError(null);
    setProgressInfo({ percent: 5, message: 'Iniciando particionado de mensajes...', currentBatch: 0, totalBatches: 0, dateRange: '', tokens: 0 });

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
                setStats({
                  total_messages: event.total_messages,
                  total_words: event.total_words,
                  participants: event.participants,
                  total_chunks: event.total_chunks
                });
                setProgressInfo(prev => ({
                  ...prev,
                  percent: event.percent,
                  totalBatches: event.total_chunks,
                  message: `Estructura lista: ${event.total_messages.toLocaleString()} mensajes en ${event.total_chunks} fragmentos.`
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
                loadSavedDossiers();
              } else if (event.type === 'error') {
                setError(event.message);
              }
            } catch (err) {
              console.error("SSE parse error", err);
            }
          }
        }
      }
    } catch (err) {
      setError(`Error durante el análisis: ${err.message}.`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDossier = async (filename) => {
    try {
      const res = await fetch(`${backendUrl}/whatsapp/dossiers/${filename}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedDossier(data);
      }
    } catch (e) {
      alert("Error al cargar el dossier");
    }
  };

  const handleExportMarkdown = () => {
    if (!analysis && !stats) return;

    let md = `# Dossier de Inteligencia y Contactos (WhatsApp)\n\n`;
    if (stats) {
      md += `## Estadísticas Globales\n- Mensajes Analizados: ${stats.total_messages?.toLocaleString() || 0}\n- Palabras: ${stats.total_words?.toLocaleString() || 0}\n\n`;
      md += `### Participantes\n`;
      stats.participants?.forEach(p => {
        md += `- **${p.name}**: ${p.message_count} mensajes (${p.percentage}%)\n`;
      });
      md += `\n`;
    }

    if (analysis?.participantes) {
      md += `## Perfiles de Contactos Extraídos\n`;
      analysis.participantes.forEach(p => {
        md += `### 👤 ${p.nombre}\n`;
        md += `- **Cumpleaños**: ${p.cumpleanos || 'No mencionado'}\n`;
        md += `- **Ubicación**: ${p.direccion_ubicacion || 'No mencionada'}\n`;
        md += `- **Profesión / Estudios**: ${p.profesion_ocupacion || 'No mencionada'}\n`;
        if (p.intereses_hobbies?.length) {
          md += `- **Intereses**: ${p.intereses_hobbies.join(', ')}\n`;
        }
        if (p.notas_clave?.length) {
          md += `- **Hechos y Anécdotas Clave**:\n`;
          p.notas_clave.forEach(n => md += `  • ${n}\n`);
        }
        md += `\n`;
      });
    }

    if (analysis?.eventos_y_compromisos?.length) {
      md += `## Cronograma de Eventos y Compromisos\n`;
      analysis.eventos_y_compromisos.forEach(ev => {
        md += `- **[${ev.fecha || 'Fecha'}]:** ${ev.descripcion}\n`;
      });
      md += `\n`;
    }

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dossier_whatsapp.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const [obsidianStatus, setObsidianStatus] = useState('');
  const [syncingObsidian, setSyncingObsidian] = useState(false);

  const handleExportObsidian = async () => {
    setSyncingObsidian(true);
    setObsidianStatus('Sincronizando con Obsidian Vault...');
    try {
      const res = await fetch(`${backendUrl}/whatsapp/export-obsidian`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok) {
        setObsidianStatus(`✓ Sincronizado en ${data.vault_path} (${data.total_contacts} contactos y agenda de eventos)`);
        setTimeout(() => setObsidianStatus(''), 4500);
      } else {
        setObsidianStatus(`⚠️ ${data.detail || 'Error al exportar'}`);
        setTimeout(() => setObsidianStatus(''), 4000);
      }
    } catch (e) {
      setObsidianStatus(`⚠️ Error: ${e.message}`);
      setTimeout(() => setObsidianStatus(''), 4000);
    } finally {
      setSyncingObsidian(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header & Subtabs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <MessageSquare size={24} style={{ color: '#10b981' }} />
            WhatsApp Intelligence & Obsidian CRM Studio
          </h2>
          <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
            Procesamiento inteligente por batches para conversaciones masivas (hasta 1M+ tokens) sincronizado con tu base de datos Obsidian.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {obsidianStatus && (
            <span style={{ fontSize: '12px', color: '#10b981', fontWeight: '600' }}>
              {obsidianStatus}
            </span>
          )}

          <button
            onClick={handleExportObsidian}
            disabled={syncingObsidian}
            className="btn-secondary"
            title="Exportar todos los contactos y eventos a tu bóveda de Obsidian (~/Documents/Obsidian_WhatsApp_CRM)"
            style={{ fontSize: '13px', padding: '8px 14px', backgroundColor: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.4)', color: '#a5b4fc' }}
          >
            <Sparkles size={14} style={{ color: '#818cf8' }} />
            <span>{syncingObsidian ? 'Sincronizando...' : '🔮 Sincronizar con Obsidian (CRM)'}</span>
          </button>

          <button
            onClick={() => { setActiveSubTab('analyzer'); setSelectedDossier(null); }}
            className={activeSubTab === 'analyzer' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '13px', padding: '8px 16px' }}
          >
            <Sparkles size={14} />
            <span>Analizador</span>
          </button>
          <button
            onClick={() => { setActiveSubTab('saved'); loadSavedDossiers(); }}
            className={activeSubTab === 'saved' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '13px', padding: '8px 16px' }}
          >
            <FolderArchive size={14} />
            <span>Dossiers Guardados ({savedDossiers.length})</span>
          </button>
        </div>
      </div>

      {activeSubTab === 'analyzer' && (
        <>
          {/* Main Upload / Input Card */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <label className="btn-secondary" style={{ cursor: 'pointer', backgroundColor: 'var(--bg-tertiary)' }}>
                  <Upload size={15} style={{ color: '#10b981' }} />
                  <span>Cargar archivo .txt de WhatsApp</span>
                  <input type="file" accept=".txt" onChange={handleFileUpload} style={{ display: 'none' }} />
                </label>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  {fileName ? `Archivo: ${fileName}` : 'o pega la transcripción en el recuadro'}
                </span>
              </div>

              {analysis && (
                <button onClick={handleExportMarkdown} className="btn-secondary">
                  <Download size={14} style={{ color: '#10b981' }} />
                  <span>Descargar Dossier (.md)</span>
                </button>
              )}
            </div>

            {/* Chat Textarea */}
            <textarea
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              placeholder="Pega aquí la transcripción del chat de WhatsApp (ej: 15/01/23, 14:30 - Juan: Hola...)..."
              style={{
                width: '100%',
                height: '140px',
                backgroundColor: 'var(--bg-input)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                fontSize: '13px',
                fontFamily: 'var(--font-mono)',
                resize: 'vertical',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />

            {/* Bottom Trigger Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '14px', fontSize: '12px', color: 'var(--text-muted)' }}>
                <span>{chatText ? `${chatText.split('\n').length.toLocaleString()} líneas cargadas` : 'Ningún chat cargado'}</span>
                <span>&bull;</span>
                <span>Chunking: <strong>150 msgs / batch</strong></span>
              </div>

              <button
                onClick={handleStreamAnalysis}
                disabled={!chatText.trim() || loading}
                className="btn-primary"
                style={{ padding: '12px 28px', fontSize: '14px' }}
              >
                {loading ? <Cpu className="animate-spin" size={16} /> : <Zap size={16} />}
                <span>{loading ? 'Procesando Batches con IA Local...' : '🚀 Iniciar Análisis por Batches'}</span>
              </button>
            </div>
          </div>

          {/* Real-time Progress Bar & Radar */}
          {loading && (
            <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #10b981' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="live-dot" />
                  <span style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>
                    {progressInfo.message || 'Procesando...'}
                  </span>
                </div>
                <span style={{ fontWeight: '800', fontSize: '15px', color: '#10b981' }}>
                  {progressInfo.percent}%
                </span>
              </div>

              {/* Progress Track */}
              <div style={{ width: '100%', height: '10px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '999px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${progressInfo.percent}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #10b981, #059669)',
                    borderRadius: '999px',
                    transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: '0 0 12px rgba(16, 185, 129, 0.5)'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
                <span>Fragmento: <strong style={{ color: 'var(--text-primary)' }}>{progressInfo.currentBatch} / {progressInfo.totalBatches}</strong></span>
                {progressInfo.dateRange && <span>Ventana Temporal: <strong style={{ color: '#10b981' }}>{progressInfo.dateRange}</strong></span>}
                <span>Tokens LLM: <strong style={{ color: 'var(--text-primary)' }}>{progressInfo.tokens.toLocaleString()}</strong></span>
              </div>
            </div>
          )}

          {error && (
            <div style={{ padding: '16px', backgroundColor: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fb7185', borderRadius: 'var(--radius-md)', fontSize: '14px' }}>
              ⚠️ {error}
            </div>
          )}

          {/* Chat Overview Statistics */}
          {stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <div className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px' }}>
                  <span>Mensajes Analizados</span>
                  <MessageSquare size={16} style={{ color: '#10b981' }} />
                </div>
                <h3 style={{ margin: '8px 0 0', fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {stats.total_messages?.toLocaleString()}
                </h3>
              </div>

              <div className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px' }}>
                  <span>Palabras Totales</span>
                  <FileText size={16} style={{ color: '#6366f1' }} />
                </div>
                <h3 style={{ margin: '8px 0 0', fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {stats.total_words?.toLocaleString()}
                </h3>
              </div>

              <div className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px' }}>
                  <span>Participantes</span>
                  <User size={16} style={{ color: '#f59e0b' }} />
                </div>
                <h3 style={{ margin: '8px 0 0', fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {stats.participants?.length || 0}
                </h3>
              </div>

              <div className="glass-panel" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px' }}>
                  <span>Batches Procesados</span>
                  <Layers size={16} style={{ color: '#06b6d4' }} />
                </div>
                <h3 style={{ margin: '8px 0 0', fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)' }}>
                  {stats.total_chunks || progressInfo.totalBatches}
                </h3>
              </div>
            </div>
          )}

          {/* Extracted Contact Profiles */}
          {analysis?.participantes && analysis.participantes.length > 0 && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '18px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  👤 Perfiles y Notas Acumuladas
                </h3>
                <span className="badge badge-emerald">Extracción Automática</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {analysis.participantes.map((p, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-card)',
                      borderRadius: 'var(--radius-md)',
                      padding: '18px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        color: '#10b981',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: '700',
                        fontSize: '14px'
                      }}>
                        {p.nombre ? p.nombre.charAt(0).toUpperCase() : 'U'}
                      </div>
                      <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>
                        {p.nombre}
                      </h4>
                    </div>

                    <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px', color: 'var(--text-secondary)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Calendar size={14} style={{ color: '#f59e0b' }} />
                        <span><strong>Cumpleaños:</strong> {p.cumpleanos || 'No mencionado'}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <MapPin size={14} style={{ color: '#f43f5e' }} />
                        <span><strong>Ubicación:</strong> {p.direccion_ubicacion || 'No mencionada'}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Briefcase size={14} style={{ color: '#6366f1' }} />
                        <span><strong>Ocupación:</strong> {p.profesion_ocupacion || 'No mencionada'}</span>
                      </div>

                      {p.intereses_hobbies?.length > 0 && (
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginTop: '2px' }}>
                          <Heart size={14} style={{ color: '#ec4899', marginTop: '3px' }} />
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {p.intereses_hobbies.map((h, hIdx) => (
                              <span key={hIdx} className="badge badge-indigo">{h}</span>
                            ))}
                          </div>
                        </div>
                      )}

                      {p.notas_clave?.length > 0 && (
                        <div style={{ marginTop: '8px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                          <strong style={{ color: 'var(--text-primary)', fontSize: '12px' }}>📝 Historial de Hechos y Anécdotas:</strong>
                          <ul style={{ margin: '6px 0 0', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
                            {p.notas_clave.map((n, nIdx) => (
                              <li key={nIdx}>{n}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Events & Chronology Cards */}
          {analysis && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
              {analysis.eventos_y_compromisos?.length > 0 && (
                <div className="glass-panel" style={{ padding: '24px' }}>
                  <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Calendar size={18} style={{ color: '#f59e0b' }} />
                    Cronograma de Eventos y Compromisos
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {analysis.eventos_y_compromisos.map((ev, idx) => (
                      <div key={idx} style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)', fontSize: '13px' }}>
                        <strong style={{ color: '#f59e0b' }}>[{ev.fecha || 'Fecha'}]:</strong> {ev.descripcion}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysis.cronologia_resumenes?.length > 0 && (
                <div className="glass-panel" style={{ padding: '24px' }}>
                  <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={18} style={{ color: '#06b6d4' }} />
                    Evolución Cronológica
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '360px', overflowY: 'auto' }}>
                    {analysis.cronologia_resumenes.map((st, idx) => (
                      <div key={idx} style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-card)', fontSize: '12px' }}>
                        <strong style={{ color: '#10b981' }}>🗓️ {st.etapa}</strong>
                        <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)' }}>{st.resumen}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Saved Dossiers Tab */}
      {activeSubTab === 'saved' && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '18px' }}>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)' }}>
              📁 Dossiers Guardados en Local (~/.ai_cli_whatsapp)
            </h3>
          </div>

          {savedDossiers.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', textAlign: 'center', margin: '40px 0' }}>
              No hay dossiers guardados todavía. Analiza una conversación arriba y se almacenará automáticamente.
            </p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: selectedDossier ? '320px 1fr' : '1fr', gap: '20px' }}>
              {/* Dossiers List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {savedDossiers.map(d => (
                  <div
                    key={d.id}
                    onClick={() => handleViewDossier(d.file_md)}
                    style={{
                      padding: '14px',
                      backgroundColor: selectedDossier?.filename === d.file_md ? 'var(--bg-tertiary)' : 'var(--bg-input)',
                      border: selectedDossier?.filename === d.file_md ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>👤 {d.title}</strong>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      {(d.size_bytes / 1024).toFixed(1)} KB &bull; {new Date(d.modified * 1000).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>

              {/* Dossier Preview Panel */}
              {selectedDossier && (
                <div style={{ backgroundColor: 'var(--bg-input)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                    <h4 style={{ margin: 0, fontSize: '15px', color: 'var(--text-primary)' }}>📄 {selectedDossier.filename}</h4>
                    <button
                      onClick={() => {
                        const blob = new Blob([selectedDossier.content], { type: 'text/markdown' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = selectedDossier.filename;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="btn-secondary"
                    >
                      <Download size={13} />
                      <span>Descargar Markdown</span>
                    </button>
                  </div>

                  <div style={{ maxHeight: '520px', overflowY: 'auto', padding: '10px 4px' }}>
                    <MarkdownView content={selectedDossier.content} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default WhatsAppAnalyzer;
