import { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  Server, 
  Database, 
  Sliders, 
  Check, 
  RefreshCw, 
  ShieldCheck, 
  Zap, 
  Trash2 
} from 'lucide-react';

function Settings() {
  const [modelInfo, setModelInfo] = useState(null);
  const [backendHealth, setBackendHealth] = useState(null);
  const [temperature, setTemperature] = useState(() => parseFloat(localStorage.getItem('ai_cli_temp') || '0.7'));
  const [maxTokens, setMaxTokens] = useState(() => parseInt(localStorage.getItem('ai_cli_max_tokens') || '40960'));
  const [systemPrompt, setSystemPrompt] = useState(() => localStorage.getItem('ai_cli_sys_prompt') || 'Eres un asistente de redacción y edición académica profesional. Estructura siempre tus respuestas en formato Markdown (.md) riguroso (usando # para títulos principales, ## para secciones, ### para subsecciones/casos, tablas Markdown con | ... |, y viñetas claras con sangría), compatible con estándares y Normas APA 7.');
  const [testingPing, setTestingPing] = useState(false);
  const [pingResult, setPingResult] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');

  const fetchStatus = async () => {
    try {
      const healthRes = await fetch('http://localhost:3094/health');
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setBackendHealth(healthData);
      } else {
        setBackendHealth({ status: 'offline' });
      }

      const modelRes = await fetch('http://localhost:3094/model/info');
      if (modelRes.ok) {
        const modelData = await modelRes.json();
        setModelInfo(modelData);
      }
    } catch (e) {
      setBackendHealth({ status: 'offline' });
      setModelInfo(null);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleTestPing = async () => {
    setTestingPing(true);
    setPingResult(null);
    const start = performance.now();

    try {
      const res = await fetch('http://localhost:3094/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Responde únicamente con la palabra: LISTO',
          max_tokens: 10
        })
      });

      const elapsed = Math.round(performance.now() - start);
      if (res.ok) {
        setPingResult({ success: true, latency: elapsed });
      } else {
        setPingResult({ success: false, error: `HTTP ${res.status}` });
      }
    } catch (e) {
      setPingResult({ success: false, error: e.message });
    } finally {
      setTestingPing(false);
    }
  };

  const handleSavePreferences = () => {
    localStorage.setItem('ai_cli_temp', temperature.toString());
    localStorage.setItem('ai_cli_max_tokens', maxTokens.toString());
    localStorage.setItem('ai_cli_sys_prompt', systemPrompt);
    setStatusMessage('✓ Parámetros guardados correctamente.');
    setTimeout(() => setStatusMessage(''), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <SettingsIcon size={24} style={{ color: '#10b981' }} />
          Panel de Control y Diagnóstico del Sistema
        </h2>
        <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '13px' }}>
          Monitorea los servicios locales, aceleración por GPU ROCm y ajusta los hiperparámetros de inferencia.
        </p>
      </div>

      {/* System Service Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Backend Card */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Server size={20} style={{ color: '#10b981' }} />
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>FastAPI Backend</h3>
            </div>
            <span className={`badge ${backendHealth?.status === 'healthy' ? 'badge-emerald' : 'badge-amber'}`}>
              {backendHealth?.status === 'healthy' ? '● ONLINE' : '○ OFFLINE'}
            </span>
          </div>

          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div><strong>Puerto:</strong> :3094</div>
            <div><strong>Versión:</strong> {backendHealth?.version || '1.0.0'}</div>
            <div><strong>LLM Bridge:</strong> {backendHealth?.llama_url || 'http://127.0.0.1:1234'}</div>
          </div>
        </div>

        {/* LLM Engine Card */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Cpu size={20} style={{ color: '#6366f1' }} />
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>llama-server</h3>
            </div>
            <span className={`badge ${modelInfo?.status === 'online' ? 'badge-emerald' : 'badge-amber'}`}>
              {modelInfo?.status === 'online' ? '● ONLINE' : '○ OFFLINE'}
            </span>
          </div>

          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div><strong>Modelo:</strong> {modelInfo?.model || 'Qwen3.5 (localmodel)'}</div>
            <div><strong>Aceleración:</strong> AMD ROCm (RX 6600 GPU)</div>
            <div><strong>Contexto:</strong> 40,960 tokens</div>
          </div>
        </div>

        {/* Security & Privacy Card */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={20} style={{ color: '#10b981' }} />
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>Privacidad Local</h3>
            </div>
            <span className="badge badge-emerald">100% AISLADO</span>
          </div>

          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div><strong>Telemetría:</strong> Deshabilitada</div>
            <div><strong>Tráfico Externo:</strong> Bloqueado (0 peticiones a la nube)</div>
            <div><strong>Dossiers:</strong> Cifrado local en filesystem</div>
          </div>
        </div>
      </div>

      {/* Latency & Ping Test */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <strong style={{ fontSize: '14px', color: 'var(--text-primary)' }}>Test de Latencia con el Modelo Local</strong>
          <p style={{ margin: '3px 0 0', fontSize: '12px', color: 'var(--text-muted)' }}>
            Envía un token de prueba a llama-server para medir el tiempo de respuesta en GPU.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {pingResult && (
            <span style={{ fontSize: '13px', fontWeight: '600', color: pingResult.success ? '#10b981' : '#f43f5e' }}>
              {pingResult.success ? `✓ Respuesta en ${pingResult.latency} ms` : `✗ ${pingResult.error}`}
            </span>
          )}

          <button onClick={handleTestPing} disabled={testingPing} className="btn-secondary">
            <RefreshCw size={14} className={testingPing ? 'animate-spin' : ''} />
            <span>{testingPing ? 'Midiendo...' : 'Ejecutar Ping'}</span>
          </button>
        </div>
      </div>

      {/* Inference Parameters */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>
            ⚙️ Hiperparámetros de Inferencia
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Temperature Slider */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Temperatura:</span>
              <strong style={{ color: '#10b981' }}>{temperature}</strong>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.5"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              style={{ accentColor: '#10b981', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Valores bajos (0.1 - 0.3) son mejores para extracción y datos exactos; valores altos (0.7+) para redacción creativa.
            </span>
          </div>

          {/* Max Tokens / Context Limit Slider */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Límite de Tokens (Generación / Contexto):</span>
              <strong style={{ color: '#10b981' }}>{maxTokens.toLocaleString()} tokens {maxTokens >= 40000 ? '(40K)' : maxTokens >= 30000 ? '(30K Compaction)' : ''}</strong>
            </div>
            <input
              type="range"
              min="512"
              max="40960"
              step="512"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value))}
              style={{ accentColor: '#10b981', cursor: 'pointer' }}
            />
            {/* Quick Presets */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {[
                { label: '4K', val: 4096 },
                { label: '8K', val: 8192 },
                { label: '16K', val: 16384 },
                { label: '30K (Compactación)', val: 30720 },
                { label: '40K (Máximo)', val: 40960 }
              ].map(preset => (
                <button
                  key={preset.val}
                  type="button"
                  onClick={() => setMaxTokens(preset.val)}
                  style={{
                    padding: '2px 8px',
                    fontSize: '11px',
                    borderRadius: '4px',
                    border: maxTokens === preset.val ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                    background: maxTokens === preset.val ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-card)',
                    color: maxTokens === preset.val ? '#10b981' : 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Soporte de contexto extendido hasta 40k tokens. A los 30k tokens (~120.000 caracteres) se activa la compactación automática inteligente.
            </span>
          </div>
        </div>

        {/* System Prompt Customization */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
            System Prompt Global Predeterminado:
          </label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            style={{
              width: '100%',
              height: '80px',
              backgroundColor: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '12px',
              fontSize: '13px',
              outline: 'none',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {/* Save Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: '#10b981', fontWeight: '600' }}>
            {statusMessage}
          </span>

          <button onClick={handleSavePreferences} className="btn-primary">
            <Check size={14} />
            <span>Guardar Configuración</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;
