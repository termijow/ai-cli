import { useState } from 'react';
import { 
  Languages, 
  ArrowLeftRight, 
  Copy, 
  Check, 
  Download, 
  Sparkles, 
  Cpu, 
  Volume2 
} from 'lucide-react';

function TranslateTool() {
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLang, setSourceLang] = useState('es');
  const [targetLang, setTargetLang] = useState('en');
  const [tone, setTone] = useState('professional'); // 'professional', 'casual', 'technical', 'academic'
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const languages = [
    { code: 'es', name: 'Español' },
    { code: 'en', name: 'Inglés' },
    { code: 'fr', name: 'Francés' },
    { code: 'de', name: 'Alemán' },
    { code: 'pt', name: 'Portugués' },
    { code: 'it', name: 'Italiano' },
    { code: 'ja', name: 'Japonés' },
    { code: 'zh', name: 'Chino' },
    { code: 'ru', name: 'Ruso' },
    { code: 'ar', name: 'Árabe' },
  ];

  const tones = [
    { id: 'professional', label: 'Profesional / Formal' },
    { id: 'casual', label: 'Coloquial / Fluido' },
    { id: 'technical', label: 'Técnico / Ingeniería' },
    { id: 'academic', label: 'Académico' },
  ];

  const handleSwap = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setSourceText(translatedText);
    setTranslatedText(sourceText);
  };

  const handleTranslate = async () => {
    if (!sourceText.trim()) return;

    setLoading(true);
    setTranslatedText('');

    const targetLangName = languages.find(l => l.code === targetLang)?.name || targetLang;
    const toneDescription = {
      professional: 'Mantén un tono profesional, elegante y corporativo.',
      casual: 'Usa un tono natural, moderno y coloquial.',
      technical: 'Conserva la terminología técnica y de programación con precisión.',
      academic: 'Usa un vocabulario riguroso, formal y académico.'
    }[tone];

    const prompt = `Traduce el siguiente texto al idioma ${targetLangName}.\nEstilo: ${toneDescription}\nResponde exclusivamente con la traducción directa.`;

    try {
      const res = await fetch('http://localhost:3094/documents/text/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: sourceText,
          target_language: targetLangName,
          prompt: prompt,
          max_tokens: 3000
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTranslatedText(data.translatedText || data.result || 'Sin traducción');
    } catch (err) {
      setTranslatedText(`Error en traducción: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Languages size={24} style={{ color: '#10b981' }} />
          Traductor Multilingüe Inteligente
        </h2>
        <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
          Traducción neural de alta fidelidad con adaptación de tono y terminología 100% en local.
        </p>
      </div>

      {/* Language Bar & Controls */}
      <div className="glass-panel" style={{ padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        {/* Languages Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            value={sourceLang}
            onChange={(e) => setSourceLang(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            {languages.map(l => (
              <option key={l.code} value={l.code}>{l.name}</option>
            ))}
          </select>

          <button
            onClick={handleSwap}
            title="Intercambiar idiomas"
            className="btn-secondary"
            style={{ padding: '8px', borderRadius: '50%' }}
          >
            <ArrowLeftRight size={14} />
          </button>

          <select
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-tertiary)',
              color: '#10b981',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px',
              fontSize: '13px',
              fontWeight: '700',
              cursor: 'pointer',
              outline: 'none'
            }}
          >
            {languages.map(l => (
              <option key={l.code} value={l.code}>{l.name}</option>
            ))}
          </select>
        </div>

        {/* Tone Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Tono:</span>
          {tones.map(t => (
            <button
              key={t.id}
              onClick={() => setTone(t.id)}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: tone === t.id ? '#10b981' : 'var(--bg-tertiary)',
                color: tone === t.id ? '#fff' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: '600'
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Translation Dual-Pane */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Source Box */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>Texto de Entrada</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{sourceText.length} caracteres</span>
          </div>

          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Escribe o pega el texto a traducir..."
            style={{
              width: '100%',
              minHeight: '380px',
              backgroundColor: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
              fontSize: '14px',
              lineHeight: '1.6',
              fontFamily: 'var(--font-sans)',
              resize: 'vertical',
              outline: 'none',
              boxSizing: 'border-box'
            }}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={handleTranslate}
              disabled={!sourceText.trim() || loading}
              className="btn-primary"
            >
              {loading ? <Cpu className="animate-spin" size={15} /> : <Sparkles size={15} />}
              <span>{loading ? 'Traduciendo...' : 'Traducir Texto'}</span>
            </button>
          </div>
        </div>

        {/* Target Translation Box */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>Traducción</span>
            <span style={{ fontSize: '12px', color: '#10b981', fontWeight: '600' }}>
              {languages.find(l => l.code === targetLang)?.name}
            </span>
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
              fontSize: '14px',
              lineHeight: '1.7',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}
          >
            {translatedText || (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '120px' }}>
                <Languages size={36} style={{ margin: '0 auto 10px', opacity: 0.3 }} />
                <p>La traducción aparecerá aquí en tiempo real.</p>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              onClick={() => {
                navigator.clipboard.writeText(translatedText);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              disabled={!translatedText}
              className="btn-secondary"
            >
              {copied ? <Check size={14} style={{ color: '#10b981' }} /> : <Copy size={14} />}
              <span>{copied ? 'Copiado' : 'Copiar'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TranslateTool;
