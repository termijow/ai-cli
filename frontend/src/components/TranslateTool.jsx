import { useState } from 'react';

function TranslateTool() {
  const [sourceText, setSourceText] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(false);

  const backendUrl = 'http://localhost:3094';

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Español' },
    { code: 'fr', name: 'Français' },
    { code: 'de', name: 'Deutsch' },
    { code: 'it', name: 'Italiano' },
    { code: 'pt', name: 'Português' },
    { code: 'ru', name: 'Русский' },
    { code: 'ja', name: '日本語' },
    { code: 'zh', name: '中文' },
  ];

  const handleTranslate = async () => {
    if (!sourceText.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/documents/${sourceLanguage}/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          text: sourceText,
          targetLanguage: targetLanguage
        })
      });

      const data = await response.json();
      setTranslatedText(data.translatedText || data.result || '');
    } catch (error) {
      setTranslatedText('Error al traducir. Asegúrate de que el backend esté en http://localhost:3094');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2 style={{ fontSize: '24px', color: '#333', marginBottom: '20px' }}>Traducir Texto</h2>

      {/* Source Language */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
          Idioma de origen
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
          value={sourceLanguage}
          onChange={(e) => setSourceLanguage(e.target.value)}
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>
      </div>

      {/* Target Language */}
      <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
          Idioma de destino
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
          value={targetLanguage}
          onChange={(e) => setTargetLanguage(e.target.value)}
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>
      </div>

      {/* Source Text */}
      <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
          Texto original
        </label>
        <textarea
          className="textarea"
          style={{
            width: '100%',
            height: '150px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            padding: '12px',
            fontSize: '14px',
            resize: 'vertical',
            fontFamily: 'inherit'
          }}
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
          placeholder="Escribe o pega el texto que quieres traducir..."
        />
      </div>

      {/* Button */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          className="btn btn-primary"
          onClick={handleTranslate}
          disabled={!sourceText || loading}
          style={{
            padding: '12px 30px',
            fontSize: '14px'
          }}
        >
          {loading ? '🔄 Traduciendo...' : '🌐 Traducir'}
        </button>
      </div>

      {/* Translated Text */}
      {translatedText && (
        <div style={{ marginTop: '20px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <label style={{ display: 'block', marginBottom: '10px', color: '#666', fontSize: '13px' }}>
            Traducción a {languages.find(l => l.code === targetLanguage)?.name}
          </label>
          <div className="code" style={{ backgroundColor: '#f9f9f9', borderRadius: '4px', padding: '15px', border: '1px solid #eee', overflowX: 'auto' }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {translatedText}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default TranslateTool;
