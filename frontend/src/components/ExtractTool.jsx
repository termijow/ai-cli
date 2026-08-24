import { useState } from 'react';
import { 
  Search, 
  Users, 
  Calendar, 
  DollarSign, 
  Key, 
  Code, 
  Copy, 
  Check, 
  Download, 
  Sparkles, 
  Cpu 
} from 'lucide-react';

function ExtractTool() {
  const [inputText, setInputText] = useState('');
  const [extractType, setExtractType] = useState('entities'); // 'entities', 'dates', 'numbers', 'summary', 'custom'
  const [customPrompt, setCustomPrompt] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const categories = [
    { id: 'entities', label: 'Personas & Entidades', icon: Users, desc: 'Nombres, empresas, lugares y marcas' },
    { id: 'dates', label: 'Fechas & Cronología', icon: Calendar, desc: 'Plazos, reuniones, eventos y citas' },
    { id: 'numbers', label: 'Métricas & Precios', icon: DollarSign, desc: 'Cifras, porcentajes, montos y KPIs' },
    { id: 'summary', label: 'Insights Clave', icon: Key, desc: 'Los 5 puntos críticos y conclusiones' },
    { id: 'custom', label: 'Esquema Personalizado', icon: Code, desc: 'Instrucción o JSON schema libre' },
  ];

  const handleExtract = async () => {
    if (!inputText.trim()) return;

    setLoading(true);
    setResult('');

    try {
      const res = await fetch('http://localhost:3094/documents/text/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: inputText,
          extract_type: extractType,
          prompt: extractType === 'custom' ? customPrompt : undefined,
          max_tokens: 2500
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data.extractedData || data.result || 'Sin datos extraídos');
    } catch (err) {
      setResult(`Error al extraer datos: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadJSON = () => {
    const blob = new Blob([result], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extraccion_${extractType}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Search size={24} style={{ color: '#10b981' }} />
          Extractor de Datos Estructurados
        </h2>
        <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
          Convierte texto no estructurado en entidades, fechas, métricas y esquemas JSON listos para usar.
        </p>
      </div>

      {/* Category Pills */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {categories.map(cat => {
          const Icon = cat.icon;
          const isSelected = extractType === cat.id;
          return (
            <div
              key={cat.id}
              onClick={() => setExtractType(cat.id)}
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
                <Icon size={18} style={{ color: isSelected ? '#10b981' : 'var(--text-muted)' }} />
                <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{cat.label}</strong>
              </div>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted)' }}>{cat.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Custom Schema Prompt if selected */}
      {extractType === 'custom' && (
        <div className="glass-panel" style={{ padding: '16px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-primary)' }}>
            Instrucciones o Campos a Extraer:
          </label>
          <input
            type="text"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Ej: Extrae { cliente, direccion_envio, items: [{ producto, precio, cantidad }], total_factura }"
            style={{
              width: '100%',
              backgroundColor: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              fontSize: '13px',
              outline: 'none',
              boxSizing: 'border-box'
            }}
          />
        </div>
      )}

      {/* Dual Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Source Text Input */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>Texto de Entrada</span>

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Pega aquí contratos, facturas, mensajes, correos o notas para extraer información estructurada..."
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

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={handleExtract}
              disabled={!inputText.trim() || loading}
              className="btn-primary"
            >
              {loading ? <Cpu className="animate-spin" size={15} /> : <Sparkles size={15} />}
              <span>{loading ? 'Extrayendo...' : 'Extraer Datos'}</span>
            </button>
          </div>
        </div>

        {/* Structured Output */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>Resultado Estructurado</span>
            {result && <span className="badge badge-emerald">JSON / Formateado</span>}
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
              fontFamily: 'var(--font-mono)',
              lineHeight: '1.6',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}
          >
            {result || (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '120px', fontFamily: 'var(--font-sans)' }}>
                <Search size={36} style={{ margin: '0 auto 10px', opacity: 0.3 }} />
                <p>Las entidades y datos estructurados aparecerán aquí.</p>
              </div>
            )}
          </div>

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
              <span>{copied ? 'Copiado' : 'Copiar'}</span>
            </button>

            <button
              onClick={handleDownloadJSON}
              disabled={!result}
              className="btn-secondary"
            >
              <Download size={14} />
              <span>Guardar JSON</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExtractTool;
