import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChevronDown, ChevronRight, Brain, Copy, Check } from 'lucide-react';

export function parseThinking(text) {
  if (!text) return { thinking: null, content: '' };

  // 1. Handle Gemma channel thought format: <|channel>thought ... <channel|>
  const gemmaMatch = text.match(/<\|channel\>thought\s*([\s\S]*?)<channel\|>/i);
  if (gemmaMatch) {
    const thinking = gemmaMatch[1].trim();
    const content = text.replace(/<\|channel\>thought\s*[\s\S]*?<channel\|>/i, '').trim();
    return { thinking, content };
  }

  // 2. Handle standard <think> ... </think> tags
  const thinkMatch = text.match(/<think>([\s\S]*?)<\/think>/i);
  if (thinkMatch) {
    const thinking = thinkMatch[1].trim();
    const content = text.replace(/<think>[\s\S]*?<\/think>/i, '').trim();
    return { thinking, content };
  }

  // 3. Handle open-ended or unmatched <think>
  if (text.startsWith('<think>')) {
    const parts = text.split(/<\/think>/i);
    if (parts.length > 1) {
      return { thinking: parts[0].replace(/<think>/i, '').trim(), content: parts.slice(1).join('</think>').trim() };
    }
  }

  return { thinking: null, content: text };
}

export default function MarkdownView({ content, style = {} }) {
  const [showThinking, setShowThinking] = useState(false);
  const [copiedCode, setCopiedCode] = useState(null);

  const { thinking, content: cleanContent } = parseThinking(content);

  const handleCopyCode = (codeText, idx) => {
    navigator.clipboard.writeText(codeText);
    setCopiedCode(idx);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', ...style }}>
      {/* Collapsible Thinking Accordion */}
      {thinking && (
        <div style={{
          backgroundColor: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
          transition: 'all 0.2s ease'
        }}>
          <button
            onClick={() => setShowThinking(!showThinking)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 12px',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: '#818cf8',
              fontSize: '12px',
              fontWeight: '600',
              textAlign: 'left'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Brain size={14} style={{ color: '#818cf8' }} />
              <span>Proceso de Razonamiento (Thinking Process)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ fontSize: '11px', opacity: 0.8 }}>{showThinking ? 'Ocultar' : 'Desplegar'}</span>
              {showThinking ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </div>
          </button>

          {showThinking && (
            <div style={{
              padding: '10px 14px',
              borderTop: '1px solid rgba(99, 102, 241, 0.15)',
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              fontSize: '12px',
              lineHeight: '1.6',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
              whiteSpace: 'pre-wrap',
              maxHeight: '350px',
              overflowY: 'auto'
            }}>
              {thinking}
            </div>
          )}
        </div>
      )}

      {/* Formatted Markdown Content */}
      <div className="markdown-rendered-content" style={{ lineHeight: '1.7', fontSize: '14px' }}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node, ...props }) => <h1 style={{ fontSize: '20px', fontWeight: '800', margin: '16px 0 8px', color: 'var(--text-primary)' }} {...props} />,
            h2: ({ node, ...props }) => <h2 style={{ fontSize: '17px', fontWeight: '700', margin: '14px 0 6px', color: 'var(--text-primary)' }} {...props} />,
            h3: ({ node, ...props }) => <h3 style={{ fontSize: '15px', fontWeight: '600', margin: '12px 0 4px', color: 'var(--text-primary)' }} {...props} />,
            p: ({ node, ...props }) => <p style={{ margin: '0 0 10px' }} {...props} />,
            ul: ({ node, ...props }) => <ul style={{ margin: '0 0 10px 20px', paddingLeft: '4px' }} {...props} />,
            ol: ({ node, ...props }) => <ol style={{ margin: '0 0 10px 20px', paddingLeft: '4px' }} {...props} />,
            li: ({ node, ...props }) => <li style={{ margin: '4px 0' }} {...props} />,
            strong: ({ node, ...props }) => <strong style={{ fontWeight: '700', color: 'var(--text-primary)' }} {...props} />,
            blockquote: ({ node, ...props }) => (
              <blockquote style={{
                borderLeft: '3px solid #10b981',
                paddingLeft: '12px',
                margin: '10px 0',
                color: 'var(--text-secondary)',
                fontStyle: 'italic',
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
                padding: '6px 12px',
                borderRadius: '0 4px 4px 0'
              }} {...props} />
            ),
            table: ({ node, ...props }) => (
              <div style={{ overflowX: 'auto', margin: '12px 0' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }} {...props} />
              </div>
            ),
            th: ({ node, ...props }) => (
              <th style={{ borderBottom: '2px solid var(--border-subtle)', padding: '8px 12px', textAlign: 'left', fontWeight: '700', color: 'var(--text-primary)', backgroundColor: 'var(--bg-tertiary)' }} {...props} />
            ),
            td: ({ node, ...props }) => (
              <td style={{ borderBottom: '1px solid var(--border-subtle)', padding: '8px 12px', color: 'var(--text-secondary)' }} {...props} />
            ),
            code: ({ node, inline, className, children, ...props }) => {
              if (inline) {
                return (
                  <code style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    color: '#10b981',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontFamily: 'var(--font-mono)'
                  }} {...props}>
                    {children}
                  </code>
                );
              }
              const codeString = String(children).replace(/\n$/, '');
              return (
                <div style={{
                  position: 'relative',
                  margin: '12px 0',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: '#090d16',
                  border: '1px solid var(--border-subtle)',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '6px 12px',
                    backgroundColor: 'rgba(255, 255, 255, 0.03)',
                    borderBottom: '1px solid var(--border-subtle)',
                    fontSize: '11px',
                    color: 'var(--text-muted)'
                  }}>
                    <span>Código</span>
                    <button
                      onClick={() => handleCopyCode(codeString, codeString.substring(0, 10))}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px'
                      }}
                    >
                      {copiedCode === codeString.substring(0, 10) ? (
                        <>
                          <Check size={12} style={{ color: '#10b981' }} />
                          <span style={{ color: '#10b981' }}>Copiado</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copiar</span>
                        </>
                      )}
                    </button>
                  </div>
                  <pre style={{
                    padding: '14px',
                    margin: 0,
                    overflowX: 'auto',
                    fontSize: '13px',
                    fontFamily: 'var(--font-mono)',
                    color: '#e2e8f0',
                    lineHeight: '1.5'
                  }}>
                    <code>{children}</code>
                  </pre>
                </div>
              );
            }
          }}
        >
          {cleanContent || ''}
        </ReactMarkdown>
      </div>
    </div>
  );
}
