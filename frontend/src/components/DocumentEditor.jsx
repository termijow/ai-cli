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
  CornerDownLeft,
  Save,
  Trash2,
  FolderGit2,
  CheckCircle2,
  RotateCcw
} from 'lucide-react';
import MarkdownView from './MarkdownView';

// Helper to render inline markdown (**bold**, *italic*, `code`)
function renderFormattedInline(text) {
  if (!text) return text;
  const parts = [];
  const regex = /(\*\*\*(.+?)\*\*\*)|(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`([^`]+)`)/g;
  let lastIndex = 0;
  let match;
  let idx = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    if (match[2]) {
      parts.push(<strong key={idx++}><em>{match[2]}</em></strong>);
    } else if (match[4]) {
      parts.push(<strong key={idx++}>{match[4]}</strong>);
    } else if (match[6]) {
      parts.push(<em key={idx++}>{match[6]}</em>);
    } else if (match[8]) {
      parts.push(<code key={idx++} style={{ fontFamily: 'monospace', backgroundColor: '#f1f5f9', padding: '1px 4px', borderRadius: '3px', fontSize: '0.9em' }}>{match[8]}</code>);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

// Word / PDF Page Sheet Parser according to APA 7th Edition
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

      // Check Markdown Table (| Col 1 | Col 2 |) or TSV table
      const isMdTable = trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|');
      const isTsvTable = trimmed.includes('\t') && i + 1 < lines.length && lines[i+1].includes('\t');

      if (isMdTable || isTsvTable) {
        flushParagraph();
        const tableLines = [];
        if (isMdTable) {
          while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
            tableLines.append ? tableLines.push(lines[i].trim()) : tableLines.push(lines[i].trim());
            i++;
          }
        } else {
          while (i < lines.length && lines[i].includes('\t')) {
            tableLines.push(lines[i].trim());
            i++;
          }
        }

        const tableRows = [];
        tableLines.forEach(tline => {
          if (/^\|(\s*:?-+:?\s*\|)+$/.test(tline)) return; // Skip separator line |---|---|
          const cells = isMdTable
            ? tline.split('|').slice(1, -1).map(c => c.trim())
            : tline.split('\t').map(c => c.trim());
          if (cells.length > 0 && cells.some(c => c.length > 0)) tableRows.push(cells);
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
      // Check Markdown #### H4
      else if (trimmed.startsWith('#### ')) {
        flushParagraph();
        elements.push({ type: 'h4', text: trimmed.replace(/^####\s+/, '') });
        isFirstRealLine = false;
      }
      // Check Blockquote (> Cita)
      else if (trimmed.startsWith('> ')) {
        flushParagraph();
        elements.push({ type: 'quote', text: trimmed.replace(/^>\s+/, '') });
        isFirstRealLine = false;
      }
      // Check Major Numbered Section (e.g. "1. Introducción y Definición", "2. Beneficios")
      else if (/^\d+\.\s*([A-ZÁÉÍÓÚÑa-záéíóúñ].*)?$/.test(trimmed) && trimmed.length < 120 && !trimmed.endsWith('.')) {
        flushParagraph();
        elements.push({ type: 'h2', text: trimmed });
        isFirstRealLine = false;
      }
      // Check Sub-Section Numbered (e.g. "1.1. Concepto y Alcance", "1.2. Diferenciación...")
      else if (/^\d+\.\d+\.?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ].*)?$/.test(trimmed) && trimmed.length < 120 && !trimmed.endsWith('.')) {
        flushParagraph();
        elements.push({ type: 'h3', text: trimmed });
        isFirstRealLine = false;
      }
      // Bullet points
      else if (/^[-*•]\s+/.test(trimmed)) {
        flushParagraph();
        elements.push({ type: 'li', text: trimmed.replace(/^[-*•]\s+/, '') });
        isFirstRealLine = false;
      }
      // Numbered items (1. Item, 2. Item)
      else if (/^\d+\.\s+/.test(trimmed)) {
        flushParagraph();
        elements.push({ type: 'ol', text: trimmed });
        isFirstRealLine = false;
      }
      // First line of document if it looks like a Title (short, no period)
      else if (isFirstRealLine && trimmed.length < 140 && !trimmed.endsWith('.')) {
        flushParagraph();
        elements.push({ type: 'h1', text: trimmed });
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
  const [documents, setDocuments] = useState(() => {
    try {
      const cached = localStorage.getItem('ai_cli_documents');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {}
    return [
      {
        id: '1',
        title: 'Documento_1.docx',
        type: 'docx',
        content: `# Informe Ejecutivo sobre la Implementación de Inteligencia Artificial Local

## 1. Introducción y Definición
### 1.1. Concepto y Alcance
La inteligencia artificial local se refiere al despliegue de modelos de aprendizaje automático y redes neuronales en dispositivos físicos dentro de una organización o infraestructura privada, sin depender de servidores centralizados en la nube. Este enfoque prioriza la ejecución del procesamiento de datos en el sitio donde se generan, garantizando un control directo sobre el ciclo de vida de la información.

### 1.2. Diferenciación vs. Soluciones en la Nube
A diferencia de las soluciones SaaS tradicionales, la IA local elimina la dependencia de conexiones a internet constantes para la inferencia de modelos. Esto permite una operación autónoma y reduce la latencia en la transmisión de datos, facilitando aplicaciones críticas que requieren respuestas inmediatas.

## 2. Beneficios Estratégicos
### 2.1. Privacidad y Cumplimiento Normativo
Al mantener los datos dentro de la red perimetral, se mitigan riesgos asociados a la filtración o el almacenamiento en servidores externos. Esto es crucial para sectores regulados como la salud o la banca, cumpliendo con normativas como el RGPD y otras leyes de protección de datos.

### 2.2. Optimización de Costos y Recursos
La inferencia local permite amortizar la inversión en hardware dedicado (como GPUs AMD Radeon con ROCm), eliminando tarifas recurrentes por token o suscripciones mensuales en la nube.

| Factor | Solución Local | Solución Nube |
| :--- | :--- | :--- |
| **Privacidad** | Totalmente aislada en hardware propio | Servidores y proveedores de terceros |
| **Latencia** | Inmediata sin dependencia de red | Dependiente de conexión a internet |
| **Costos** | Inversión fija amortizable | Facturación recurrente por token |

## 3. Conclusiones y Próximos Pasos
Se recomienda proceder con la instalación de la suite local para el análisis de documentos y transcripciones masivas.`,
        chatHistory: []
      }
    ];
  });

  const [activeDocId, setActiveDocId] = useState(() => {
    return localStorage.getItem('ai_cli_active_doc_id') || '1';
  });

  const [viewMode, setViewMode] = useState('word'); // 'word' (Word Page Sheet) | 'editor' (Textarea)
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState('');
  const [copied, setCopied] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [lastSavedTime, setLastSavedTime] = useState(null);
  const [savingStatus, setSavingStatus] = useState('idle'); // 'idle' | 'saving' | 'saved'

  // Text selection states
  const [selectedText, setSelectedText] = useState('');
  const [targetSelection, setTargetSelection] = useState(null); // The exact text snippet sent to AI
  const [floatingToolbarPos, setFloatingToolbarPos] = useState(null);
  const promptInputRef = useRef(null);

  const activeDoc = documents.find(d => d.id === activeDocId) || documents[0] || {
    id: '1',
    title: 'Documento_1.docx',
    type: 'docx',
    content: '',
    chatHistory: []
  };

  const chatHistory = activeDoc.chatHistory || [];

  // Fetch documents from persistent backend workspace on mount
  useEffect(() => {
    const loadWorkspace = async () => {
      try {
        const res = await fetch('http://localhost:3094/documents/workspace');
        if (res.ok) {
          const data = await res.json();
          if (data.documents && data.documents.length > 0) {
            setDocuments(data.documents);
            const savedActiveId = localStorage.getItem('ai_cli_active_doc_id');
            const exists = data.documents.some(d => d.id === savedActiveId);
            setActiveDocId(exists ? savedActiveId : data.documents[0].id);
          }
        }
      } catch (err) {
        console.warn('Could not connect to backend workspace, using cached state:', err);
      }
    };
    loadWorkspace();
  }, []);

  // Save active document ID whenever it changes
  useEffect(() => {
    localStorage.setItem('ai_cli_active_doc_id', activeDocId);
    setAiResponse('');
    setSelectedText('');
    setTargetSelection(null);
  }, [activeDocId]);

  // Helper to persist document to disk backend & localStorage
  const persistActiveDoc = async (docToSave) => {
    if (!docToSave) return;
    try {
      setSavingStatus('saving');
      // 1. LocalStorage for immediate tab reload resilience
      localStorage.setItem('ai_cli_documents', JSON.stringify(documents));

      // 2. Persistent folder /documents for git tracking
      await fetch('http://localhost:3094/documents/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: docToSave.id,
          title: docToSave.title,
          content: docToSave.content,
          type: docToSave.type || 'docx',
          chatHistory: docToSave.chatHistory || [],
          updated_at: new Date().toISOString()
        })
      });

      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setLastSavedTime(timeStr);
      setSavingStatus('saved');
    } catch (err) {
      console.warn('Persist error:', err);
      setSavingStatus('error');
    }
  };

  // Auto-save every 10 seconds (without git commit)
  useEffect(() => {
    const autoSaveTimer = setInterval(() => {
      if (activeDoc) {
        persistActiveDoc(activeDoc);
      }
    }, 10000); // 10s auto-save interval

    return () => clearInterval(autoSaveTimer);
  }, [documents, activeDoc]);

  const updateActiveContent = (newContent) => {
    setDocuments(prev => prev.map(doc => doc.id === activeDoc.id ? { ...doc, content: newContent } : doc));
  };

  const handleCreateDocument = async () => {
    const newId = Date.now().toString();
    const newDoc = {
      id: newId,
      title: `Documento_${documents.length + 1}.docx`,
      type: 'docx',
      content: '# Título del Documento\n\n## 1. Introducción\nEscribe aquí tu contenido...',
      chatHistory: []
    };
    const updated = [...documents, newDoc];
    setDocuments(updated);
    setActiveDocId(newId);
    setAiResponse('');
    setSelectedText('');
    setTargetSelection(null);

    // Save to disk immediately
    persistActiveDoc(newDoc);
  };

  const handleCloseDocument = async (id, e) => {
    e.stopPropagation();
    if (documents.length <= 1) return;
    const nextDocs = documents.filter(d => d.id !== id);
    setDocuments(nextDocs);
    localStorage.setItem('ai_cli_documents', JSON.stringify(nextDocs));

    if (activeDocId === id) {
      setActiveDocId(nextDocs[0].id);
    }

    try {
      await fetch(`http://localhost:3094/documents/workspace/${id}`, { method: 'DELETE' });
    } catch (err) {
      console.warn('Error deleting document from workspace:', err);
    }
  };

  const handleClearDocChat = () => {
    if (window.confirm(`¿Deseas vaciar el historial de chat de "${activeDoc.title}"?`)) {
      const updatedDocs = documents.map(d => d.id === activeDoc.id ? { ...d, chatHistory: [] } : d);
      setDocuments(updatedDocs);
      persistActiveDoc({ ...activeDoc, chatHistory: [] });
      setStatusMessage('✓ Historial de chat vaciado.');
      setTimeout(() => setStatusMessage(''), 2000);
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
        content: data.content || '',
        chatHistory: []
      };

      const updated = [...documents, importedDoc];
      setDocuments(updated);
      setActiveDocId(newId);
      setStatusMessage(`✓ ${file.name} importado y guardado.`);
      setTimeout(() => setStatusMessage(''), 3000);

      // Persist imported doc
      persistActiveDoc(importedDoc);
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

  // Ask AI with target selection context & per-document chat persistence
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
    
    // Add user message to current doc's chat history
    const historyWithUser = [...(activeDoc.chatHistory || []), userMsg];
    setDocuments(prev => prev.map(d => d.id === activeDoc.id ? { ...d, chatHistory: historyWithUser } : d));

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
          system_prompt: savedSysPrompt || 'Eres un redactor y editor académico y profesional de documentos. Responde siempre con formato Markdown (.md) estructurado (títulos #, ##, ###, tablas | ... |, viñetas con sangría) bajo estándares de Normas APA 7.'
        })
      });

      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      const replyContent = data.reply || data.response || 'Sin respuesta';
      setAiResponse(replyContent);

      const assistantMsg = {
        role: 'assistant',
        content: replyContent,
        tokens: data.tokens_used,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      const finalHistory = [...historyWithUser, assistantMsg];
      const updatedDoc = { ...activeDoc, chatHistory: finalHistory };
      
      setDocuments(prev => prev.map(d => d.id === activeDoc.id ? updatedDoc : d));
      setPrompt('');

      // Immediately persist to disk folder documents/
      persistActiveDoc(updatedDoc);
    } catch (err) {
      const errMsg = `Error de conexión con el LLM: ${err.message}`;
      setAiResponse(errMsg);
      const errorMsg = { role: 'assistant', content: errMsg, isError: true, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
      const historyWithError = [...historyWithUser, errorMsg];
      setDocuments(prev => prev.map(d => d.id === activeDoc.id ? { ...d, chatHistory: historyWithError } : d));
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
    setStatusMessage('Generando Word (.docx con Normas APA)...');

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
      setStatusMessage('✓ Word (.docx) descargado con formato APA 7.');
      setTimeout(() => setStatusMessage(''), 3000);
    } catch (err) {
      alert(`Error al generar Word: ${err.message}`);
      setStatusMessage('');
    }
  };

  const handleExportPdf = async () => {
    if (!activeDoc.content.trim()) return;
    setStatusMessage('Generando PDF (Normas APA 7)...');

    try {
      const res = await fetch('http://localhost:3094/documents/pdf/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: activeDoc.title.replace(/\.[^/.]+$/, ''),
          content: activeDoc.content
        })
      });

      if (!res.ok) throw new Error('Error al generar PDF');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${activeDoc.title.replace(/\.[^/.]+$/, '')}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setStatusMessage('✓ PDF (.pdf) descargado con formato APA 7.');
      setTimeout(() => setStatusMessage(''), 3000);
    } catch (err) {
      alert(`Error al generar PDF: ${err.message}`);
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
          {/* Git Auto-save Indicator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(16, 185, 129, 0.09)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              padding: '4px 9px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              color: '#10b981',
              fontWeight: '500'
            }}
            title="Se guarda automáticamente cada 10s en la carpeta /documents de tu proyecto para que puedas hacer git commit / git push."
          >
            <FolderGit2 size={13} style={{ color: '#10b981' }} />
            <span>
              {savingStatus === 'saving'
                ? 'Guardando en documents/...'
                : (lastSavedTime ? `Autoguardado: ${lastSavedTime} (documents/)` : 'Autoguardado cada 10s')}
            </span>
          </div>

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
          <button onClick={handleExportDocx} className="btn-secondary" title="Exportar a Word con formato APA 7" style={{ fontSize: '12px', padding: '6px 10px' }}>
            <FileDown size={13} style={{ color: '#2563eb' }} />
            <span>Word (.docx)</span>
          </button>

          {/* Export PDF (.pdf) */}
          <button onClick={handleExportPdf} className="btn-secondary" title="Exportar a PDF con formato APA 7" style={{ fontSize: '12px', padding: '6px 10px' }}>
            <FileText size={13} style={{ color: '#ef4444' }} />
            <span>PDF (.pdf)</span>
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
                    maxWidth: '760px',
                    minHeight: '920px',
                    backgroundColor: '#ffffff',
                    color: '#000000',
                    fontFamily: '"Times New Roman", Times, serif',
                    padding: '60px 70px',
                    borderRadius: '2px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.4), 0 0 0 1px rgba(0,0,0,0.1)',
                    boxSizing: 'border-box',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative'
                  }}
                >
                  {/* APA 7 Top-Right Page Header */}
                  <div style={{
                    position: 'absolute',
                    top: '28px',
                    right: '55px',
                    fontSize: '10pt',
                    color: '#475569',
                    fontFamily: '"Times New Roman", Times, serif'
                  }}>
                    {page.pageNumber}
                  </div>

                  {/* Page Sheet Content Rendered Strictly under APA 7 Norms */}
                  <div style={{ flex: 1, fontFamily: '"Times New Roman", Times, serif', color: '#000000' }}>
                    {page.elements.map((el, elIdx) => {
                      if (el.type === 'h1') {
                        return (
                          <h1
                            key={elIdx}
                            style={{
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '15pt',
                              fontWeight: '700',
                              color: '#000000',
                              textAlign: 'center',
                              margin: elIdx === 0 ? '0 0 16px 0' : '22px 0 12px 0',
                              lineHeight: '1.3'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </h1>
                        );
                      }
                      if (el.type === 'h2') {
                        return (
                          <h2
                            key={elIdx}
                            style={{
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '13pt',
                              fontWeight: '700',
                              color: '#000000',
                              margin: '18px 0 8px 0',
                              lineHeight: '1.35',
                              textAlign: 'left'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </h2>
                        );
                      }
                      if (el.type === 'h3') {
                        return (
                          <h3
                            key={elIdx}
                            style={{
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '12pt',
                              fontWeight: '700',
                              fontStyle: 'italic',
                              color: '#000000',
                              margin: '14px 0 6px 0',
                              lineHeight: '1.35',
                              textAlign: 'left'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </h3>
                        );
                      }
                      if (el.type === 'h4') {
                        return (
                          <h4
                            key={elIdx}
                            style={{
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '12pt',
                              fontWeight: '700',
                              color: '#000000',
                              margin: '10px 0 4px 28px',
                              lineHeight: '1.35',
                              textAlign: 'left'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </h4>
                        );
                      }
                      if (el.type === 'quote') {
                        return (
                          <blockquote
                            key={elIdx}
                            style={{
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '11pt',
                              fontStyle: 'italic',
                              color: '#1e293b',
                              margin: '10px 0 10px 28px',
                              paddingLeft: '14px',
                              borderLeft: '3px solid #94a3b8',
                              lineHeight: '1.5'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </blockquote>
                        );
                      }
                      if (el.type === 'table') {
                        return (
                          <div key={elIdx} style={{ margin: '16px 0', overflowX: 'auto' }}>
                            <table style={{
                              width: '100%',
                              borderCollapse: 'collapse',
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '10pt',
                              color: '#000000',
                              borderTop: '1.5px solid #000000',
                              borderBottom: '1.5px solid #000000'
                            }}>
                              <thead>
                                <tr>
                                  {el.headers.map((h, hIdx) => (
                                    <th
                                      key={hIdx}
                                      style={{
                                        borderBottom: '1px solid #000000',
                                        padding: '7px 10px',
                                        textAlign: 'left',
                                        fontWeight: '700',
                                        color: '#000000',
                                        fontSize: '10pt'
                                      }}
                                    >
                                      {renderFormattedInline(h)}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {el.rows.map((row, rIdx) => (
                                  <tr key={rIdx}>
                                    {row.map((cell, cIdx) => (
                                      <td
                                        key={cIdx}
                                        style={{
                                          padding: '6px 10px',
                                          color: '#000000',
                                          fontSize: '10pt',
                                          verticalAlign: 'top'
                                        }}
                                      >
                                        {renderFormattedInline(cell)}
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
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '12pt',
                              fontWeight: '400',
                              color: '#000000',
                              margin: '4px 0 4px 28px',
                              lineHeight: '1.6'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </li>
                        );
                      }
                      if (el.type === 'ol') {
                        return (
                          <div
                            key={elIdx}
                            style={{
                              fontFamily: '"Times New Roman", Times, serif',
                              fontSize: '12pt',
                              fontWeight: '400',
                              color: '#000000',
                              margin: '4px 0 4px 28px',
                              lineHeight: '1.6'
                            }}
                          >
                            {renderFormattedInline(el.text)}
                          </div>
                        );
                      }
                      return (
                        <p
                          key={elIdx}
                          style={{
                            fontFamily: '"Times New Roman", Times, serif',
                            fontSize: '12pt',
                            fontWeight: '400',
                            color: '#000000',
                            margin: '0 0 10px 0',
                            lineHeight: '1.65'
                          }}
                        >
                          {renderFormattedInline(el.text)}
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {chatHistory.length > 0 && (
                <button
                  onClick={handleClearDocChat}
                  style={{
                    background: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '3px 8px',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px',
                    transition: 'all 0.15s ease'
                  }}
                  title="Vaciar el historial de chat de este documento"
                >
                  <Trash2 size={12} />
                  <span>Limpiar Chat</span>
                </button>
              )}
              <span className="badge badge-emerald">Qwen Local</span>
            </div>
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
              onClick={() => handleAskAI('Reestructura, formatea y organiza este contenido en formato Markdown (.md) riguroso según Normas APA 7 (usa # para título central, ## para secciones, ### para subsecciones, tablas Markdown | ... | para comparativas/factores, y viñetas - **Concepto:** Detalle). Devuelve directamente el texto limpio y listo para documento.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px', borderColor: '#10b981', color: '#10b981' }}
            >
              📐 Formato APA (.md)
            </button>
            <button
              onClick={() => handleAskAI('Escribe un informe ejecutivo estructurado en Markdown (#, ##, ###) sobre este documento. Sin preámbulos.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              📊 Resumir
            </button>
            <button
              onClick={() => handleAskAI('Corrige la redacción, ortografía y estilo para que tenga un tono formal y claro. Escribe directamente el texto final en Markdown.')}
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
              onClick={() => handleAskAI('Genera una tabla comparativa Markdown clara y concisa (| Col 1 | Col 2 |) que resuma y contraste los puntos clave de este documento. Responde directamente con la tabla.')}
              disabled={loading || !activeDoc.content.trim()}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 9px' }}
            >
              📊 Tabla Comparativa
            </button>
            <button
              onClick={() => handleAskAI('Extrae las fechas, personas y conclusiones principales en viñetas claras (- **Punto:** Detalle).')}
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
