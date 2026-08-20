import { useState, useEffect } from 'react';

function Settings() {
  const [backendUrl, setBackendUrl] = useState('http://localhost:3094');
  const [llamaUrl, setLlamaUrl] = useState('http://localhost:1234');
  const [llamaModel, setLlamaModel] = useState('llama-3.2-1b-instruct.Q4_K_M.gguf');
  const [useSystemPrompt, setUseSystemPrompt] = useState(true);
  const [systemPrompt, setSystemPrompt] = useState('Eres un asistente de IA útil para analizar documentos. Responde de manera clara y concisa.');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);

  const [saving, setSaving] = useState(false);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:3094/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          backendUrl,
          llamaUrl,
          llamaModel,
          useSystemPrompt,
          systemPrompt,
          temperature,
          maxTokens
        })
      });

      if (!response.ok) throw new Error('Error guardando configuraciones');
      alert('Configuraciones guardadas exitosamente');
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const resetSettings = () => {
    if (window.confirm('¿Estás seguro de que quieres restablecer a las configuraciones por defecto?')) {
      setBackendUrl('http://localhost:3094');
      setLlamaUrl('http://localhost:1234');
      setLlamaModel('llama-3.2-1b-instruct.Q4_K_M.gguf');
      setUseSystemPrompt(true);
      setSystemPrompt('Eres un asistente de IA útil para analizar documentos. Responde de manera clara y concisa.');
      setTemperature(0.7);
      setMaxTokens(2048);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h2 style={{ fontSize: '24px', color: '#333', marginBottom: '20px' }}>Configuración</h2>

      {/* Backend Settings */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <h3 style={{ fontSize: '16px', color: '#333', marginBottom: '15px' }}>🌐 Backend Settings</h3>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
            URL del Backend API
          </label>
          <input
            type="text"
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
            URL del Llama.cpp
          </label>
          <input
            type="text"
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
            value={llamaUrl}
            onChange={(e) => setLlamaUrl(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
            Modelo Llama
          </label>
          <input
            type="text"
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
            value={llamaModel}
            onChange={(e) => setLlamaModel(e.target.value)}
          />
        </div>
      </div>

      {/* AI Settings */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginTop: '20px' }}>
        <h3 style={{ fontSize: '16px', color: '#333', marginBottom: '15px' }}>🤖 AI Settings</h3>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
            Usar Prompt de Sistema
          </label>
          <input
            type="checkbox"
            checked={useSystemPrompt}
            onChange={(e) => setUseSystemPrompt(e.target.checked)}
            style={{ marginRight: '10px' }}
          />
          <button
            className="btn btn-secondary"
            onClick={() => setUseSystemPrompt(false)}
            style={{ marginLeft: '20px', padding: '8px 15px', fontSize: '12px' }}
          >
            Desactivar
          </button>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
            Prompt de Sistema
          </label>
          <textarea
            style={{
              width: '100%',
              height: '80px',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px',
              resize: 'vertical'
            }}
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
              Temperatura: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', color: '#666', fontSize: '13px' }}>
              Máximo Tokens: {maxTokens}
            </label>
            <input
              type="range"
              min="256"
              max="4096"
              step="256"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value))}
            />
          </div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          className="btn btn-primary"
          onClick={saveSettings}
          disabled={saving}
          style={{
            padding: '12px 30px',
            fontSize: '14px'
          }}
        >
          {saving ? '💾 Guardando...' : '💾 Guardar Configuración'}
        </button>

        <button
          className="btn btn-secondary"
          onClick={resetSettings}
          style={{
            marginLeft: '15px',
            padding: '12px 30px',
            fontSize: '14px'
          }}
        >
          🔄 Restablecer
        </button>
      </div>
    </div>
  );
}

export default Settings;
