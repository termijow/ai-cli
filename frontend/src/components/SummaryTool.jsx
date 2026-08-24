import { useState } from 'react';
import { 
  FileSpreadsheet, 
  Sparkles, 
  Copy, 
  Check, 
  FileDown, 
  Sliders, 
  Layers, 
  Cpu, 
  ArrowRight,
  BookOpen
} from 'lucide-react';
import MarkdownView from './MarkdownView';

function SummaryTool() {
  const [inputText, setInputText] = useState('');
  const [summaryType, setSummaryType] = useState('executive'); // 'executive', 'bullets', 'actions', 'table'
  const [summaryLength, setSummaryLength] = useState('medium'); // 'short', 'medium', 'long'
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [tokensUsed, setTokensUsed] = useState(0);

  const types = [
    { id: 'executive', label: 'Resumen Ejecutivo', icon: '👔', desc: 'Visión estratégica en prosa fluida' },
    { id: 'bullets', label: 'Puntos Clave', icon: '🎯', desc: 'Viñetas con las ideas centrales' },
    { id: 'actions', label: 'Acciones y Tareas', icon: '✅', desc: 'Lista de compromisos y entregables' },
    { id: 'table', label: 'Estructura Markdown', icon: '📊', desc: 'Organizado en secciones y tablas' },
  ];

  const handleSummarize = async () => {
    if (!inputText.trim()) return;

    setLoading(true);
    setResult('');

    const lengthPrompt = {
      short: 'Sé muy sintético y conciso (máximo 1-2 párrafos o 5 viñetas).',
      medium: 'Proporciona un resumen balanceado y completo (3-4 párrafos o 8 viñetas).',
      long: 'Realiza un análisis exhaustivo y detallado cubriendo todos los aspectos del documento.'
    }[summaryLength];

    const typePrompt = {
      executive: 'Escribe un resumen ejecutivo claro y profesional con introducción, desarrollo y conclusión.',
      bullets: 'Extrae los puntos clave más importantes en una lista de viñetas claras y directas.',
      actions: 'Extrae todas las decisiones, tareas pendientes, acuerdos y próximos pasos.',
      table: 'Organiza el resumen con títulos de sección Markdown y tablas donde sea pertinente.'
    }[summaryType];

    const fullPrompt = `${typePrompt}\n${lengthPrompt}`;

    try {
      const res = await fetch('http://localhost:3094/documents/text/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: inputText,
          summary_type: summaryType,
          prompt: fullPrompt,
          max_tokens: summaryLength === 'long' ? 3500 : 2048
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data.summary || data.result || 'Sin contenido');
      setTokensUsed(data.tokens_used || 0);
    } catch (err) {
      setResult(`Error al resumir: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExportWord = async () => {
    if (!result) return;
    try {
      const res = await fetch('http://localhost:3094/documents/word/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Resumen Ejecutivo AI-CLI',
          content: result
        })
      });

      if (!res.ok) throw new Error('Error al generar DOCX');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Resumen_Ejecutivo.docx';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleExportPdf = async () => {
    if (!result) return;
    try {
      const res = await fetch('http://localhost:3094/documents/pdf/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Resumen Ejecutivo AI-CLI',
          content: result
        })
      });

      if (!res.ok) throw new Error('Error al generar PDF');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Resumen_Ejecutivo.pdf';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };


  const wordCount = inputText.trim() ? inputText.trim().split(/\s+/).length : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Tool Header */}
      <div>
        <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileSpreadsheet size={24} style={{ color: '#10b981' }} />
          Estudio de Resumen Ejecutivo
        </h2>
        <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
          Sintetiza documentos, artículos o reportes con precisión mediante modelos de lenguaje locales.
        </p>
      </div>

      {/* Preset Selectors */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
        {types.map(t => {
          const isSelected = summaryType === t.id;
          return (
            <div
              key={t.id}
              onClick={() => setSummaryType(t.id)}
              style={{
                backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                border: isSelected ? '2px solid #10b981' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                boxShadow: isSelected ? '0 0 12px rgba(16, 185, 129, 0.2)' : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ fontSize: '18px' }}>{t.icon}</span>
                <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{t.label}</strong>
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted)' }}>{t.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Dual Pane Layout (Input + Output) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Left Column: Source Text */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>Texto Original</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{wordCount.toLocaleString()} palabras</span>
          </div>

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Pega aquí el artículo, reporte, contrato o documento que deseas resumir..."
            style={{
              width: '100%',
              minHeight: '380px',
              backgroundColor: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
              fontSize: '13px',
              lineHeight: '1.6',
              fontFamily: 'var(--font-sans)',
              resize: 'vertical',
              outline: 'none',
              boxSizing: 'border-box'
            }}
          />

          {/* Controls Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {/* Length Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Extensión:</span>
              {['short', 'medium', 'long'].map(len => (
                <button
                  key={len}
                  onClick={() => setSummaryLength(len)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: summaryLength === len ? '#10b981' : 'var(--bg-tertiary)',
                    color: summaryLength === len ? '#fff' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: '600'
                  }}
                >
                  {len === 'short' ? 'Corto' : len === 'medium' ? 'Medio' : 'Extenso'}
                </button>
              ))}
            </div>

            <button
              onClick={handleSummarize}
              disabled={!inputText.trim() || loading}
              className="btn-primary"
            >
              {loading ? <Cpu className="animate-spin" size={15} /> : <Sparkles size={15} />}
              <span>{loading ? 'Resumiendo...' : 'Generar Resumen'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: AI Generated Summary */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>Resumen Generado</span>
            {tokensUsed > 0 && (
              <span className="badge badge-emerald">{tokensUsed.toLocaleString()} tokens</span>
            )}
          </div>

          <div
            style={{
              flex: 1,
              minHeight: '380px',
              backgroundColor: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              fontSize: '13px',
              lineHeight: '1.7',
              overflowY: 'auto'
            }}
          >
            {result ? (
              <MarkdownView content={result} />
            ) : (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '120px' }}>
                <BookOpen size={36} style={{ margin: '0 auto 10px', opacity: 0.3 }} />
                <p>El resumen generado por la IA aparecerá aquí.</p>
              </div>
            )}
          </div>

          {/* Result Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              onClick={() => {
                navigator.clipboard.writeText(result);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              disabled={!result}
              className="btn-secondary"
            >
              {copied ? <Check size={14} style={{ color: '#10b981' }} /> : <Copy size={14} />}
              <span>{copied ? 'Copiado' : 'Copiar Texto'}</span>
            </button>

            <button
              onClick={handleExportWord}
              disabled={!result}
              className="btn-secondary"
            >
              <FileDown size={14} style={{ color: '#2563eb' }} />
              <span>Word (.docx)</span>
            </button>

            <button
              onClick={handleExportPdf}
              disabled={!result}
              className="btn-secondary"
            >
              <FileText size={14} style={{ color: '#ef4444' }} />
              <span>PDF (.pdf)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SummaryTool;
