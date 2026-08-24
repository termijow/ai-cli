import { useState, useRef, useEffect } from 'react';
import { 
  FileText, 
  Upload, 
  Download, 
  Sparkles, 
  Plus, 
  X, 
  Copy, 
  Check, 
  FileDown, 
  Send, 
  RefreshCw, 
  Bot, 
  Eye, 
  Edit3, 
  SplitSquareVertical,
  Scissors,
  Wand2,
  Languages,
  FileCheck2,
  Layers,
  CornerDownLeft
} from 'lucide-react';
import MarkdownView from './MarkdownView';

// Word / PDF Page Sheet Parser
function parseDocumentToWordPages(rawContent) {
  if (!rawContent || !rawContent.trim()) {
    return [{ pageNumber: 1, elements: [{ type: 'p', text: 'Escribe tu documento aquí...' }] }];
  }

  // Split by explicit page breaks (--- or [Salto de página])
  const pageChunks = rawContent.split(/\n\s*---\s*\n|\n\s*\[Salto de p[aá]gina\]\s*\n/i);

  return pageChunks.map((chunk, pageIndex) => {
    const rawLines = chunk.split('\n');
    // Filter out dummy filename headers like "Documento_1", "Documento_2", "Documento 2"
    const lines = rawLines.filter((l, idx) => {
      const t = l.trim();
      if (!t) return false;
      if (idx === 0 && /^Documento[_\s]\d+$/i.test(t)) return false;
      return true;
    });

    const elements = [];
    let currentParagraph = [];

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const text = currentParagraph.join(' ').trim();
        if (text) {
          elements.push({ type: 'p', text });
        }
        currentParagraph = [];
      }
    };

    let isFirstRealLine = (pageIndex === 0);
    let i = 0;

    while (i < lines.length) {
      const trimmed = lines[i].trim();
      if (!trimmed) {
        flushParagraph();
        i++;
        continue;
      }

      // Check Markdown Table (| Col 1 | Col 2 |)
      if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|')) {
        flushParagraph();
        const tableLines = [];
        while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
          tableLines.push(lines[i].trim());
          i++;
        }

        const tableRows = [];
        tableLines.forEach(tline => {
          if (/^\|(\s*:?-+:?\s*\|)+$/.test(tline)) return; // Skip separator line |---|---|
          const cells = tline.split('|').slice(1, -1).map(c => c.trim());
          if (cells.length > 0) tableRows.push(cells);
        });

        if (tableRows.length > 0) {
          elements.push({
            type: 'table',
            headers: tableRows[0],
            rows: tableRows.slice(1)
          });
        }
        isFirstRealLine = false;
        continue;
      }

      // Check Markdown # H1
      if (trimmed.startsWith('# ') && !trimmed.startsWith('## ')) {
        flushParagraph();
        elements.push({ type: 'h1', text: trimmed.replace(/^#\s+/, '') });
        isFirstRealLine = false;
      }
      // Check Markdown ## H2
      else if (trimmed.startsWith('## ') && !trimmed.startsWith('### ')) {
        flushParagraph();
        elements.push({ type: 'h2', text: trimmed.replace(/^##\s+/, '') });
        isFirstRealLine = false;
      }
      // Check Markdown ### H3
      else if (trimmed.startsWith('### ')) {
        flushParagraph();
        elements.push({ type: 'h3', text: trimmed.replace(/^###\s+/, '') });
        isFirstRealLine = false;
      }
      // Check Major Numbered Section (e.g. "1. Introducción y Definición", "2. Beneficios", "2.")
      else if (/^\d+\.\s*([A-ZÁÉÍÓÚÑa-záéíóúñ].*)?$/.test(trimmed)) {
        flushParagraph();
        elements.push({ type: 'h2', text: trimmed });
        isFirstRealLine = false;
      }
      // Check Sub-Section Numbered (e.g. "1.1. Concepto y Alcance", "1.2. Diferenciación...", "2.1. Privacidad...")
      else if (/^\d+\.\d+\.?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ].*)?$/.test(trimmed)) {
        flushParagraph();
        elements.push({ type: 'h3', text: trimmed });
        isFirstRealLine = false;
      }
      // First line of document if it looks like a Title (short, no period)
      else if (isFirstRealLine && trimmed.length < 140 && !trimmed.endsWith('.')) {
        flushParagraph();
        elements.push({ type: 'h1', text: trimmed });
        isFirstRealLine = false;
      }
      // Bullet points
      else if (/^[-*•]\s+/.test(trimmed)) {
        flushParagraph();
        elements.push({ type: 'li', text: trimmed.replace(/^[-*•]\s+/, '') });
        isFirstRealLine = false;
      }
      // Regular text
      else {
        currentParagraph.push(trimmed);
        isFirstRealLine = false;
      }

      i++;
    }

    flushParagraph();
    return { pageNumber: pageIndex + 1, elements };
  });
}

export default function DocumentEditor() {
  const [documents, setDocuments] = useState([
    {
      id: '1',
      title: 'Documento_1.docx',
      type: 'docx',
      content: `Informe Ejecutivo sobre la Implementación de Inteligencia Artificial Local

1. Introducción y Definición
1.1. Concepto y Alcance
La inteligencia artificial local se refiere al despliegue de modelos de aprendizaje automático y redes neuronales en dispositivos físicos dentro de una organización o infraestructura privada, sin depender de servidores centralizados en la nube. Este enfoque prioriza la ejecución del procesamiento de datos en el sitio donde se generan, garantizando un control directo sobre el ciclo de vida de la información.

1.2. Diferenciación vs. Soluciones en la Nube
A diferencia de las soluciones SaaS tradicionales, la IA local elimina la dependencia de conexiones a internet constantes para la inferencia de modelos. Esto permite una operación autónoma y reduce la latencia en la transmisión de datos, facilitando aplicaciones críticas que requieren respuestas inmediatas.

2. Beneficios Estratégicos
2.1. Privacidad y Cumplimiento Normativo
Al mantener los datos dentro de la red perimetral, se mitigan riesgos asociados a la filtración o el almacenamiento en servidores externos. Esto es crucial para sectores regulados como la salud o la banca, cumpliendo con normativas como el RGPD y otras leyes de protección de datos.

---

2.2. Optimización de Costos y Recursos
La inferencia local permite amortizar la inversión en hardware dedicado (como GPUs AMD Radeon con ROCm), eliminando tarifas recurrentes por token o suscripciones mensuales en la nube.

3. Conclusiones y Próximos Pasos
Se recomienda proceder con la instalación de la suite local para el análisis de documentos y transcripciones masivas.`
    }
  ]);
  const [activeDocId, setActiveDocId] = useState('1');
  const [viewMode, setViewMode] = useState('word'); // 'word' (Word Page Sheet) | 'editor' (Textarea)
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [copied, setCopied] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  // Text selection states
  const [selectedText, setSelectedText] = useState('');
  const [targetSelection, setTargetSelection] = useState(null); // The exact text snippet sent to AI
  const [floatingToolbarPos, setFloatingToolbarPos] = useState(null);
  const promptInputRef = useRef(null);

  const activeDoc = documents.find(d => d.id === activeDocId) || documents[0];

  const updateActiveContent = (newContent) => {
    setDocuments(prev => prev.map(doc => doc.id === activeDoc.id ? { ...doc, content: newContent } : doc));
  };

  const handleCreateDocument = () => {
    const newId = Date.now().toString();
    const newDoc = {
      id: newId,
      title: `Documento_${documents.length + 1}.docx`,
      type: 'docx',
      content: '# Título del Documento\n\n1. Introducción\nEscribe aquí tu contenido...'
    };
    setDocuments([...documents, newDoc]);
    setActiveDocId(newId);
    setAiResponse('');
    setSelectedText('');
    setTargetSelection(null);
  };

  const handleCloseDocument = (id, e) => {
    e.stopPropagation();
    if (documents.length <= 1) return;
    const nextDocs = documents.filter(d => d.id !== id);
    setDocuments(nextDocs);
    if (activeDocId === id) {
      setActiveDocId(nextDocs[0].id);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setStatusMessage(`Cargando ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:3094/documents/parse', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error('Error al procesar el archivo');
      const data = await res.json();

      const newId = Date.now().toString();
      const importedDoc = {
        id: newId,
        title: data.filename || file.name,
        type: data.metadata?.type || 'docx',
        content: data.content || ''
      };

      setDocuments(prev => [...prev, importedDoc]);
      setActiveDocId(newId);
      setStatusMessage(`✓ ${file.name} importado.`);
      setTimeout(() => setStatusMessage(''), 3000);
    } catch (err) {
      alert(`Error al importar archivo: ${err.message}`);
      setStatusMessage('');
    }
  };

  const handleInsertPageBreak = () => {
    const breakTag = '\n\n---\n\n';
    updateActiveContent(activeDoc.content + breakTag);
    setStatusMessage('✓ Salto de página insertado.');
    setTimeout(() => setStatusMessage(''), 2000);
  };

  // Text Selection detection on mouseup
  const handleSheetMouseUp = () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) {
      setFloatingToolbarPos(null);
      return;
    }

    const text = sel.toString().trim();
    if (text.length >= 3) {
      setSelectedText(text);
      try {
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        setFloatingToolbarPos({
          top: Math.max(10, rect.top - 46),
          left: Math.max(10, rect.left + rect.width / 2 - 130)
        });
      } catch (e) {
        setFloatingToolbarPos(null);
      }
    } else {
      setFloatingToolbarPos(null);
    }
  };

  // Ask AI with optional target selection context
  const handleAskAI = async (customInstruction, explicitSelection = null) => {
    const textContext = explicitSelection || targetSelection || selectedText;
    const instruction = customInstruction || prompt;
    if (!instruction.trim()) return;

    if (textContext) {
      setTargetSelection(textContext);
    }

    setLoading(true);
    setAiResponse('');
    setFloatingToolbarPos(null);

    const userLabel = textContext 
      ? `[Sección: "${textContext.length > 50 ? textContext.substring(0, 50) + '...' : textContext}"] ${instruction}`
      : instruction;

    const userMsg = { role: 'user', content: userLabel, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setChatHistory(prev => [...prev, userMsg]);

    const contextPayload = textContext 
      ? `Documento completo de referencia:\n${activeDoc.content}\n\nSECCIÓN ESPECÍFICA SELECCIONADA POR EL USUARIO PARA MODIFICAR:\n"${textContext}"`
      : activeDoc.content;

    try {
      const savedMaxTokens = parseInt(localStorage.getItem('ai_cli_max_tokens') || '40960');
      const savedTemp = parseFloat(localStorage.getItem('ai_cli_temp') || '0.7');
      const savedSysPrompt = localStorage.getItem('ai_cli_sys_prompt');

      const res = await fetch('http://localhost:3094/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: instruction,
          context: contextPayload,
          max_tokens: savedMaxTokens,
          temperature: savedTemp,
          system_prompt: savedSysPrompt || 'Eres un editor y redactor profesional de documentos en español. Si el usuario te pide cambios sobre una sección seleccionada, responde directamente con la versión redactada o modificada de esa sección lista para insertar, sin saludos ni explicaciones innecesarias.'
        })
      });

      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      const replyContent = data.reply || data.response || 'Sin respuesta';
      setAiResponse(replyContent);
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: replyContent,
        tokens: data.tokens_used,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
      setPrompt('');
    } catch (err) {
      const errMsg = `Error de conexión con el LLM: ${err.message}`;
      setAiResponse(errMsg);
      setChatHistory(prev => [...prev, { role: 'assistant', content: errMsg, isError: true }]);
    } finally {
      setLoading(false);
    }
  };

  const handleActionOnSelection = (actionType) => {
    if (!selectedText) return;
    setTargetSelection(selectedText);

    if (actionType === 'improve') {
      handleAskAI(`Reescribe y mejora la redacción del fragmento seleccionado para que tenga un tono formal, elegante y profesional. Devuelve únicamente el texto corregido.`, selectedText);
    } else if (actionType === 'translate') {
      handleAskAI(`Traduce al inglés formal el fragmento seleccionado. Devuelve únicamente la traducción directa.`, selectedText);
    } else if (actionType === 'expand') {
      handleAskAI(`Desarrolla y expande con más profundidad y detalle las ideas del siguiente fragmento seleccionado.`, selectedText);
    } else if (actionType === 'summarize') {
      handleAskAI(`Sintetiza y resume en puntos directos el siguiente fragmento seleccionado.`, selectedText);
    } else if (actionType === 'custom') {
      setPrompt(`Modifica la sección seleccionada para: `);
      setFloatingToolbarPos(null);
      if (promptInputRef.current) {
        promptInputRef.current.focus();
      }
    }
  };

  const handleReplaceSelection = () => {
    if (!aiResponse || !targetSelection) return;
    const clean = aiResponse.replace(/<think>[\s\S]*?<\/think>/, '').trim();

    if (activeDoc.content.includes(targetSelection)) {
      const updated = activeDoc.content.replace(targetSelection, clean);
      updateActiveContent(updated);
      setStatusMessage('✓ Selección reemplazada con éxito.');
    } else {
      // Fuzzy fallback
      updateActiveContent((activeDoc.content ? activeDoc.content + '\n\n' : '') + clean);
      setStatusMessage('✓ Insertado en el documento.');
    }
    setTargetSelection(null);
    setTimeout(() => setStatusMessage(''), 2500);
  };

  const handleInsertAtEnd = () => {
    if (!aiResponse) return;
    const clean = aiResponse.replace(/<think>[\s\S]*?<\/think>/, '').trim();
    updateActiveContent((activeDoc.content ? activeDoc.content + '\n\n' : '') + clean);
    setStatusMessage('✓ Insertado al final del documento.');
    setTimeout(() => setStatusMessage(''), 2500);
  };

  const handleReplaceDocument = () => {
    if (!aiResponse) return;
    const clean = aiResponse.replace(/<think>[\s\S]*?<\/think>/, '').trim();
    updateActiveContent(clean);
    setStatusMessage('✓ Documento reemplazado.');
    setTimeout(() => setStatusMessage(''), 2500);
  };

  const handleExportDocx = async () => {
    if (!activeDoc.content.trim()) return;
    setStatusMessage('Generando Word (.docx)...');

    try {
      const res = await fetch('http://localhost:3094/documents/word/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: activeDoc.title.replace(/\.[^/.]+$/, ''),
          content: activeDoc.content
        })
      });

      if (!res.ok) throw new Error('Error al generar DOCX');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${activeDoc.title.replace(/\.[^/.]+$/, '')}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      setStatusMessage('✓ Word (.docx) descargado.');
      setTimeout(() => setStatusMessage(''), 3000);
    } catch (err) {
      alert(`Error al generar Word: ${err.message}`);
      setStatusMessage('');
    }
  };

  const handleExportText = (format) => {
    const ext = format === 'md' ? 'md' : 'txt';
    const blob = new Blob([activeDoc.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeDoc.title.replace(/\.[^/.]+$/, '')}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Parse into Word Pages
  const pages = parseDocumentToWordPages(activeDoc.content);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', position: 'relative' }}>
      
      {/* Floating Selection Action Toolbar */}
      {floatingToolbarPos && selectedText && (
        <div
          style={{
            position: 'fixed',
            top: `${floatingToolbarPos.top}px`,
            left: `${floatingToolbarPos.left}px`,
            zIndex: 9999,
            backgroundColor: '#0f172a',
            border: '1px solid #10b981',
            borderRadius: '9999px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6), 0 0 12px rgba(16, 185, 129, 0.3)',
            padding: '4px 8px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            animation: 'fadeIn 0.15s ease'
          }}
        >
          <span style={{ fontSize: '11px', color: '#10b981', fontWeight: '700', padding: '0 4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={12} />
            <span>Selección:</span>
          </span>

          <button
            onClick={() => handleActionOnSelection('improve')}
            title="Mejorar redacción de la selección"
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              borderRadius: '9999px',
              padding: '4px 8px',
              color: '#fff',
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Wand2 size={11} style={{ color: '#10b981' }} />
            <span>Pulir</span>
          </button>

          <button
            onClick={() => handleActionOnSelection('expand')}
            title="Expandir y desarrollar contenido"
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              borderRadius: '9999px',
              padding: '4px 8px',
              color: '#fff',
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Layers size={11} style={{ color: '#6366f1' }} />
            <span>Expandir</span>
          </button>

          <button
            onClick={() => handleActionOnSelection('translate')}
            title="Traducir selección a inglés"
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              borderRadius: '9999px',
              padding: '4px 8px',
              color: '#fff',
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Languages size={11} style={{ color: '#06b6d4' }} />
            <span>EN</span>
          </button>

          <button
            onClick={() => handleActionOnSelection('custom')}
            title="Preguntar algo específico sobre esta selección"
            style={{
              background: '#10b981',
              border: 'none',
              borderRadius: '9999px',
              padding: '4px 10px',
              color: '#000',
              fontWeight: '700',
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Bot size={11} />
            <span>Pedir Cambio</span>
          </button>
        </div>
      )}

      {/* Top Document Tabs & Toolbar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'var(--bg-secondary)',
        padding: '8px 16px',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        gap: '12px',
        flexWrap: 'wrap'
      }}>
        {/* Document Tab Bar */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', overflowX: 'auto', flex: 1 }}>
          {documents.map(doc => {
            const isActive = doc.id === activeDocId;
            return (
              <div
                key={doc.id}
                onClick={() => setActiveDocId(doc.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
                  border: isActive ? '1px solid var(--border-card)' : '1px solid transparent',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: isActive ? '600' : '400',
                  color: isActive ? '#10b981' : 'var(--text-secondary)',
                  transition: 'all 0.15s ease'
                }}
              >
                <FileText size={14} style={{ color: isActive ? '#10b981' : 'var(--text-muted)' }} />
                <span>{doc.title}</span>
                {documents.length > 1 && (
                  <button
                    onClick={(e) => handleCloseDocument(doc.id, e)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', padding: '2px' }}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>
            );
          })}

          <button
            onClick={handleCreateDocument}
            title="Crear nuevo documento"
            className="btn-secondary"
            style={{ padding: '6px 10px', fontSize: '12px' }}
          >
            <Plus size={13} />
            <span>Nuevo</span>
          </button>
        </div>

        {/* Toolbar Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {statusMessage && (
            <span style={{ fontSize: '12px', color: '#10b981', fontWeight: '600' }}>
              {statusMessage}
            </span>
          )}

          {/* View Mode Toggle */}
          <div style={{ display: 'flex', backgroundColor: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
            <button
              onClick={() => setViewMode('word')}
              style={{
                padding: '5px 10px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                backgroundColor: viewMode === 'word' ? '#10b981' : 'transparent',
                color: viewMode === 'word' ? '#fff' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Eye size={13} />
              <span>Hoja Word / PDF</span>
            </button>
            <button
              onClick={() => setViewMode('editor')}
              style={{
                padding: '5px 10px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                backgroundColor: viewMode === 'editor' ? '#10b981' : 'transparent',
                color: viewMode === 'editor' ? '#fff' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Edit3 size={13} />
              <span>Editar Texto</span>
            </button>
          </div>

          {/* Insert Page Break */}
          <button onClick={handleInsertPageBreak} className="btn-secondary" title="Insertar Salto de Página (---)" style={{ fontSize: '12px', padding: '6px 10px' }}>
            <SplitSquareVertical size={13} style={{ color: '#f59e0b' }} />
            <span>Salto de Página</span>
          </button>

          {/* Import File */}
          <label className="btn-secondary" style={{ cursor: 'pointer', fontSize: '12px', padding: '6px 10px' }}>
            <Upload size={13} style={{ color: '#10b981' }} />
            <span>Importar</span>
            <input type="file" accept=".docx,.pdf,.md,.txt" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>

          {/* Export Word (.docx) */}
          <button onClick={handleExportDocx} className="btn-secondary" title="Exportar a Word (.docx)" style={{ fontSize: '12px', padding: '6px 10px' }}>
            <FileDown size={13} style={{ color: '#2563eb' }} />
            <span>Word (.docx)</span>
          </button>

          {/* Export Markdown */}
          <button onClick={() => handleExportText('md')} className="btn-secondary" title="Exportar a Markdown" style={{ fontSize: '12px', padding: '6px 10px' }}>
            <Download size={13} />
            <span>MD</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout: Word Canvas (Left) + AI Copilot (Right) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1.45fr) minmax(380px, 1fr)',
        gap: '20px',
        alignItems: 'start'
      }}>
        
        {/* Left Column: Word / PDF Page Sheet */}
        <div>
          {viewMode === 'word' ? (
            /* True A4 Word Sheet Container (No extra headers/banners) */
            <div
              onMouseUp={handleSheetMouseUp}
              style={{
                backgroundColor: '#1e293b',
                padding: '24px 16px',
                borderRadius: 'var(--radius-lg)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '20px',
                minHeight: '700px',
                overflowY: 'auto',
                userSelect: 'text'
              }}
            >
              {pages.map((page, pIdx) => (
                <div
                  key={pIdx}
                  style={{
                    width: '100%',
                    maxWidth: '740px',
                    minHeight: '880px',
                    backgroundColor: '#ffffff',
                    color: '#000000',
                    fontFamily: 'Arial, Helvetica, sans-serif',
                    padding: '55px 65px',
                    borderRadius: '2px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.4), 0 0 0 1px rgba(0,0,0,0.1)',
                    boxSizing: 'border-box',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative'
                  }}
                >
                  {/* Page Sheet Content Rendered Strictly in Arial & Pure Black (#000000) */}
                  <div style={{ flex: 1, fontFamily: 'Arial, Helvetica, sans-serif', color: '#000000' }}>
                    {page.elements.map((el, elIdx) => {
                      if (el.type === 'h1') {
                        return (
                          <h1
                            key={elIdx}
                            style={{
                              fontFamily: 'Arial, Helvetica, sans-serif',
                              fontSize: '18pt', // 24px
                              fontWeight: '700',
                              color: '#000000',
                              margin: elIdx === 0 ? '0 0 14px 0' : '20px 0 10px 0',
                              lineHeight: '1.25'
                            }}
                          >
                            {el.text}
                          </h1>
                        );
                      }
                      if (el.type === 'h2') {
                        return (
                          <h2
                            key={elIdx}
                            style={{
                              fontFamily: 'Arial, Helvetica, sans-serif',
                              fontSize: '16pt', // 21.3px
                              fontWeight: '700',
                              color: '#000000',
                              margin: '18px 0 8px 0',
                              lineHeight: '1.3'
                            }}
                          >
                            {el.text}
                          </h2>
                        );
                      }
                      if (el.type === 'h3') {
                        return (
                          <h3
                            key={elIdx}
                            style={{
                              fontFamily: 'Arial, Helvetica, sans-serif',
                              fontSize: '14pt', // 18.6px
                              fontWeight: '700',
                              color: '#000000',
                              margin: '14px 0 6px 0',
                              lineHeight: '1.35'
                            }}
                          >
                            {el.text}
                          </h3>
                        );
                      }
                      if (el.type === 'table') {
                        return (
                          <div key={elIdx} style={{ margin: '18px 0', overflowX: 'auto' }}>
                            <table style={{
                              width: '100%',
                              borderCollapse: 'collapse',
                              fontFamily: 'Arial, Helvetica, sans-serif',
                              fontSize: '11pt',
                              color: '#000000',
                              border: '1px solid #cbd5e1'
                            }}>
                              <thead>
                                <tr style={{ backgroundColor: '#f1f5f9' }}>
                                  {el.headers.map((h, hIdx) => (
                                    <th
                                      key={hIdx}
                                      style={{
                                        border: '1px solid #cbd5e1',
                                        padding: '8px 12px',
                                        textAlign: 'left',
                                        fontWeight: '700',
                                        color: '#000000',
                                        fontSize: '11pt'
                                      }}
                                    >
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {el.rows.map((row, rIdx) => (
                                  <tr key={rIdx} style={{ backgroundColor: rIdx % 2 === 1 ? '#f8fafc' : '#ffffff' }}>
                                    {row.map((cell, cIdx) => (
                                      <td
                                        key={cIdx}
                                        style={{
                                          border: '1px solid #cbd5e1',
                                          padding: '7px 12px',
                                          color: '#000000',
                                          fontSize: '11pt'
                                        }}
                                      >
                                        {cell}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        );
                      }
                      if (el.type === 'li') {
                        return (
                          <li
                            key={elIdx}
                            style={{
                              fontFamily: 'Arial, Helvetica, sans-serif',
                              fontSize: '12pt', // 16px
                              fontWeight: '400',
                              color: '#000000',
                              margin: '4px 0 4px 20px',
                              lineHeight: '1.55'
                            }}
                          >
                            {el.text}
                          </li>
                        );
                      }
                      return (
                        <p
                          key={elIdx}
                          style={{
                            fontFamily: 'Arial, Helvetica, sans-serif',
                            fontSize: '12pt', // 16px
                            fontWeight: '400', // Sin bold
                            color: '#000000', // SIEMPRE negro
                            margin: '0 0 12px 0',
                            lineHeight: '1.6'
                          }}
                        >
                          {el.text}
                        </p>
                      );
                    })}
                  </div>

                  {/* Clean Page Bottom Footer */}
                  {pages.length > 1 && (
                    <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid #e5e7eb', textAlign: 'center', fontSize: '10pt', color: '#666666', fontFamily: 'Arial, sans-serif' }}>
                      Página {pIdx + 1} de {pages.length}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            /* Direct Textarea Editor */
            <div className="glass-panel" style={{ padding: '20px' }}>
              <textarea
                value={activeDoc.content}
                onChange={(e) => updateActiveContent(e.target.value)}
                placeholder="Escribe el contenido de tu documento aquí..."
                style={{
                  width: '100%',
                  minHeight: '700px',
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '18px',
                  fontSize: '14px',
                  lineHeight: '1.7',
                  fontFamily: 'var(--font-mono)',
                  resize: 'vertical',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          )}
        </div>

        {/* Right Column: AI Assistant / Copilot */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', height: '740px', position: 'sticky', top: '75px' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={18} style={{ color: '#10b981' }} />
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)' }}>
                Asistente de Documentos
              </h3>
            </div>
            <span className="badge badge-emerald">Qwen Local</span>
          </div>

          {/* Active Target Selection Pill Indicator */}
          {(targetSelection || selectedText) && (
            <div style={{
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
                <span className="live-dot" />
                <span style={{ color: '#10b981', fontWeight: '600', whiteSpace: 'nowrap' }}>Sección seleccionada:</span>
                <span style={{ color: 'var(--text-secondary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                  "{(targetSelection || selectedText).substring(0, 40)}..."
                </span>
              </div>
              <button
                onClick={() => { setSelectedText(''); setTargetSelection(null); setFloatingToolbarPos(null); }}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}
                title="Descartar contexto de selección"
              >
                <X size={13} />
              </button>
            </div>
          )}

          {/* Quick Prompt Chips */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleAskAI('Escribe un informe ejecutivo estructurado sobre este documento. Usa títulos numerados (1., 1.1., 2.) o encabezados (#, ##, ###). Sin preámbulos.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              📊 Resumir
            </button>
            <button
              onClick={() => handleAskAI('Corrige la redacción, ortografía y estilo para que tenga un tono formal y claro. Escribe directamente el texto final.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              ✍️ Pulir Estilo
            </button>
            <button
              onClick={() => handleAskAI('Traduce este documento completo al inglés formal. Escribe directamente la traducción.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              🌐 Traducir (EN)
            </button>
            <button
              onClick={() => handleAskAI('Genera una tabla comparativa Markdown clara y concisa que resuma y contraste los puntos clave de este documento. Responde directamente con la tabla.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              📊 Tabla Comparativa
            </button>
            <button
              onClick={() => handleAskAI('Extrae las fechas, personas y conclusiones principales en viñetas claras.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              🔍 Extraer Claves
            </button>
          </div>

          {/* Chat / Response Scroll View */}
          <div style={{
            flex: 1,
            backgroundColor: 'var(--bg-input)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            padding: '14px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {chatHistory.length === 0 && !loading && (
              <div style={{ textAlign: 'center', margin: 'auto', color: 'var(--text-muted)', fontSize: '13px' }}>
                <Bot size={30} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
                <p>Selecciona texto en la hoja o escribe tu consulta para recibir asistencia.</p>
              </div>
            )}

            {chatHistory.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '95%',
                  backgroundColor: msg.role === 'user' ? '#10b981' : 'var(--bg-tertiary)',
                  color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-card)'
                }}
              >
                <div style={{ fontSize: '11px', opacity: 0.7, marginBottom: '4px', fontWeight: '600' }}>
                  {msg.role === 'user' ? 'Tú' : 'IA Asistente'} &bull; {msg.time}
                </div>
                
                {msg.role === 'assistant' ? (
                  <MarkdownView content={msg.content} />
                ) : (
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                )}
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#10b981', fontSize: '13px', padding: '10px' }}>
                <RefreshCw size={14} className="animate-spin" />
                <span>Razonando y redactando con IA local...</span>
              </div>
            )}
          </div>

          {/* Action Bar for AI Response */}
          {aiResponse && !loading && (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {targetSelection && (
                <button
                  onClick={handleReplaceSelection}
                  className="btn-primary"
                  style={{ flex: 1, justifyContent: 'center', fontSize: '12px', padding: '8px' }}
                >
                  🎯 Reemplazar en la Selección
                </button>
              )}
              <button
                onClick={handleInsertAtEnd}
                className="btn-secondary"
                style={{ flex: targetSelection ? 'initial' : 1, justifyContent: 'center', fontSize: '12px', padding: '8px' }}
              >
                📥 Insertar al final
              </button>
              <button
                onClick={handleReplaceDocument}
                className="btn-secondary"
                style={{ flex: targetSelection ? 'initial' : 1, justifyContent: 'center', fontSize: '12px', padding: '8px', color: '#f59e0b' }}
              >
                🔄 Reemplazar Todo
              </button>
              <button
                onClick={() => {
                  const clean = aiResponse.replace(/<think>[\s\S]*?<\/think>/, '').trim();
                  navigator.clipboard.writeText(clean);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="btn-secondary"
                style={{ padding: '8px' }}
                title="Copiar texto"
              >
                {copied ? <Check size={14} style={{ color: '#10b981' }} /> : <Copy size={14} />}
              </button>
            </div>
          )}

          {/* Prompt Input Form */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleAskAI(); }}
            style={{ display: 'flex', gap: '8px' }}
          >
            <input
              ref={promptInputRef}
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={targetSelection || selectedText ? `Pide cambios sobre la sección seleccionada...` : `Pide un cambio o redactar una sección...`}
              disabled={loading}
              style={{
                flex: 1,
                backgroundColor: 'var(--bg-input)',
                border: (targetSelection || selectedText) ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 14px',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              className="btn-primary"
              style={{ padding: '10px 16px' }}
            >
              <Send size={15} />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
