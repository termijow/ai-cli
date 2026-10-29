import { useState, useEffect } from 'react';
import { 
  Trophy, 
  Gamepad2, 
  Zap, 
  Clock, 
  Cpu, 
  Search, 
  Filter, 
  ExternalLink, 
  Play, 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  Flame, 
  LayoutGrid, 
  Table as TableIcon,
  Sparkles,
  Star,
  Edit3
} from 'lucide-react';

function StarRating({ value = 0, onChange, disabled = false }) {
  const [hover, setHover] = useState(0);

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
      {[1, 2, 3, 4, 5].map((star) => {
        const isFilled = (hover || value) >= star;
        return (
          <button
            key={star}
            type="button"
            disabled={disabled}
            onMouseEnter={() => !disabled && setHover(star)}
            onMouseLeave={() => !disabled && setHover(0)}
            onClick={(e) => {
              e.stopPropagation();
              if (onChange) onChange(star);
            }}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '1px',
              cursor: disabled ? 'default' : 'pointer',
              color: isFilled ? '#fbbf24' : 'rgba(255,255,255,0.2)',
              transition: 'transform 0.1s ease, color 0.1s ease',
              transform: hover === star ? 'scale(1.2)' : 'scale(1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title={`Calificar con ${star} estrellas`}
          >
            <Star size={16} fill={isFilled ? '#fbbf24' : 'none'} strokeWidth={isFilled ? 1 : 1.5} />
          </button>
        );
      })}
      <span style={{ fontSize: '11px', fontWeight: '700', color: value > 0 ? '#fbbf24' : 'var(--text-muted)', marginLeft: '4px' }}>
        {value > 0 ? `${value}★` : 'Sin Calificar'}
      </span>
    </div>
  );
}

export default function BenchmarkView() {
  const [benchmarks, setBenchmarks] = useState([]);
  const [pending, setPending] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('completed'); // 'completed', 'pending', 'all', 'playable', 'small', 'top'
  const [sortBy, setSortBy] = useState('score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [activeModalModel, setActiveModalModel] = useState(null);

  const fetchBenchmarks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/benchmarks?sort_by=${sortBy}&order=${sortOrder}`);
      if (res.ok) {
        const data = await res.json();
        setBenchmarks(data.benchmarks || []);
        setPending(data.pending || []);
        setSummary(data.summary || {});
      }
    } catch (e) {
      console.error('Error fetching benchmarks:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks();
  }, [sortBy, sortOrder]);

  const pool = filterType === 'completed'
    ? benchmarks
    : filterType === 'pending'
      ? pending
      : filterType === 'playable'
        ? benchmarks.filter(b => b.playable)
        : filterType === 'stars5'
          ? benchmarks.filter(b => (b.stars || 0) >= 4)
        : filterType === 'broken'
          ? benchmarks.filter(b => !b.playable || (b.stars || 0) <= 2)
        : filterType === 'small'
          ? [...benchmarks, ...pending].filter(b => {
              const m = b.model.toLowerCase();
              return m.includes('e4b') || m.includes('e2b') || m.includes('0.8b') || m.includes('tiny');
            })
        : filterType === 'top'
          ? benchmarks.filter(b => (b.user_rank || '').toLowerCase().includes('top') || (b.stars || 0) >= 4)
          : [...benchmarks, ...pending];

  const filteredBenchmarks = pool.filter(b => {
    const q = search.toLowerCase();
    return !q || 
      b.model.toLowerCase().includes(q) || 
      (b.user_rank || '').toLowerCase().includes(q) || 
      (b.user_review || '').toLowerCase().includes(q);
  });

  const handleRateModel = async (modelId, newStars, newPlayable = null, newReview = null) => {
    const updateList = (list) =>
      list.map((m) => {
        if (m.id === modelId || m.model === modelId) {
          const updatedStars = (newStars !== undefined && newStars !== null) ? newStars : (m.stars || 0);
          const updatedPlayable = newPlayable !== null ? newPlayable : (m.playable !== undefined ? m.playable : updatedStars >= 3);
          const updatedReview = newReview !== null ? newReview : (m.user_review || '');
          const badgeClass = updatedStars >= 5 ? 'badge-gold' :
                             updatedStars === 4 ? 'badge-emerald' :
                             updatedStars === 3 ? 'badge-cyan' :
                             updatedStars === 2 ? 'badge-amber' : 'badge-rose';
          const userRank = updatedStars >= 5 ? 'Top 5 Estrellas' :
                           updatedStars === 4 ? 'Muy Bueno (4★)' :
                           updatedStars === 3 ? 'Aceptable (3★)' :
                           updatedStars === 2 ? 'Defectuoso (2★)' : 'Roto / Inútil (1★)';
          return {
            ...m,
            stars: updatedStars,
            playable: updatedPlayable,
            user_review: updatedReview,
            badge_class: badgeClass,
            user_rank: userRank,
            rating_str: `${updatedStars}/5 (${updatedStars * 2}/10)`
          };
        }
        return m;
      });

    setBenchmarks(prev => updateList(prev));
    setPending(prev => updateList(prev));

    try {
      const payload = { stars: newStars };
      if (newPlayable !== null) payload.playable = newPlayable;
      if (newReview !== null) payload.review = newReview;

      await fetch(`/api/benchmarks/${modelId}/rating`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.error('Error saving rating:', e);
    }
  };

  const handleSortChange = (e) => {
    const val = e.target.value;
    const [field, order] = val.split('_');
    setSortBy(field);
    setSortOrder(order);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 182, 212, 0.08) 100%)',
        border: '1px solid rgba(16, 185, 129, 0.25)',
        borderRadius: '16px',
        padding: '24px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: '#fff',
              padding: '6px',
              borderRadius: '10px',
              display: 'flex'
            }}>
              <Trophy size={20} />
            </span>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)' }}>
              Arena Leaderboard & Benchmarks
            </h2>
            <span className="badge badge-emerald">Loop Engineering TDD</span>
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-muted)' }}>
            Comparativa real y automatizada de modelos locales ejecutando código de videojuegos en tiempo real en AMD ROCm.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <a
            href="/benchmarks"
            target="_blank"
            rel="noreferrer"
            style={{
              padding: '9px 16px',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              textDecoration: 'none',
              cursor: 'pointer'
            }}
          >
            <span>Dashboard Standalone</span>
            <ExternalLink size={14} />
          </a>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px'
      }}>
        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '14px',
          padding: '16px 20px'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            🏆 Top 1 Absoluto
          </div>
          <div style={{ fontSize: '18px', fontWeight: '800', color: '#fbbf24', marginTop: '6px' }}>
            Qwen 3.6 35B A3B
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            95/100 Pts | Calificación: 10/10 (Impecable)
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '14px',
          padding: '16px 20px'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            ⚡ Top 1 Compacto Turbo
          </div>
          <div style={{ fontSize: '18px', fontWeight: '800', color: '#10b981', marginTop: '6px' }}>
            Nemotron 3.5 Bolt E4B
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            100/100 Pts | 30.97 t/s con DFlash MTP
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '14px',
          padding: '16px 20px'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            🌟 Top 2 Compacto Favorito
          </div>
          <div style={{ fontSize: '18px', fontWeight: '800', color: '#06b6d4', marginTop: '6px' }}>
            Gemma 4 E4B (UD-Q6_K_XL)
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            100/100 Pts | El mejor modelo pequeño probado
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '14px',
          padding: '16px 20px'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            🎮 Modelos en Arena
          </div>
          <div style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '6px' }}>
            <span style={{ color: '#10b981' }}>{summary.total_benchmarked || benchmarks.length}</span> Evaluados / <span style={{ color: '#f59e0b' }}>{summary.total_pending || pending.length}</span> Pendientes
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Total: {summary.total_models || (benchmarks.length + pending.length)} modelos instalados
          </div>
        </div>
      </div>

      {/* Control Bar: Search, Filters, Sorting & View Toggle */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '14px',
        padding: '14px 18px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px'
      }}>
        {/* Search Input */}
        <div style={{ position: 'relative', flex: '1', minWidth: '220px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Buscar modelo o veredicto..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '9px 12px 9px 36px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none'
            }}
          />
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {[
            { id: 'completed', label: `🏆 Con Benchmark (${summary.total_benchmarked ?? benchmarks.length})` },
            { id: 'pending', label: `⏳ Sin Benchmark (${summary.total_pending ?? pending.length})` },
            { id: 'stars5', label: '⭐ Top Estrellas (4-5★)' },
            { id: 'broken', label: '❌ Rotos / Defectuosos' },
            { id: 'all', label: `Todos (${summary.total_models ?? (benchmarks.length + pending.length)})` },
            { id: 'playable', label: 'Solo Jugables' },
            { id: 'small', label: 'Compactos (E4B/E2B)' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilterType(f.id)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: filterType === f.id ? '700' : '500',
                border: '1px solid',
                borderColor: filterType === f.id ? '#10b981' : 'var(--border-subtle)',
                backgroundColor: filterType === f.id ? '#10b981' : 'var(--bg-tertiary)',
                color: filterType === f.id ? '#000' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Sort Dropdown & View Mode */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={`${sortBy}_${sortOrder}`}
            onChange={handleSortChange}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="stars_desc">⭐ Mis Estrellas: 5★ a 1★ (Recomendado)</option>
            <option value="stars_asc">⭐ Mis Estrellas: 1★ a 5★</option>
            <option value="score_desc">Puntuación TDD Sintética: Mayor a Menor</option>
            <option value="score_asc">Puntuación TDD Sintética: Menor a Mayor</option>
            <option value="speed_desc">Velocidad t/s: Más Rápido</option>
            <option value="time_asc">Tiempo Generación: Menor a Mayor</option>
            <option value="name_asc">Nombre: A - Z</option>
          </select>

          <div style={{
            display: 'flex',
            backgroundColor: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <button
              onClick={() => setViewMode('cards')}
              title="Vista Tarjetas"
              style={{
                padding: '7px 10px',
                border: 'none',
                background: viewMode === 'cards' ? 'var(--border-card)' : 'transparent',
                color: viewMode === 'cards' ? '#10b981' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              <LayoutGrid size={16} />
            </button>
            <button
              onClick={() => setViewMode('table')}
              title="Vista Tabla"
              style={{
                padding: '7px 10px',
                border: 'none',
                background: viewMode === 'table' ? 'var(--border-card)' : 'transparent',
                color: viewMode === 'table' ? '#10b981' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              <TableIcon size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
          <Sparkles className="animate-spin" size={28} style={{ color: '#10b981', margin: '0 auto 12px' }} />
          <div>Cargando evaluaciones y benchmarks de la Arena...</div>
        </div>
      ) : filteredBenchmarks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
          No se encontraron modelos con los filtros seleccionados.
        </div>
      ) : viewMode === 'cards' ? (
        /* Cards View */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '18px'
        }}>
          {filteredBenchmarks.map((b) => {
            if (b.status === 'pending') {
              return (
                <div
                  key={b.id}
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px dashed rgba(245, 158, 11, 0.45)',
                    borderRadius: '16px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                      <div>
                        <span style={{
                          fontSize: '11px',
                          fontWeight: '700',
                          padding: '3px 8px',
                          borderRadius: '999px',
                          display: 'inline-block',
                          marginBottom: '6px',
                          backgroundColor: 'rgba(245, 158, 11, 0.15)',
                          color: '#f59e0b',
                          border: '1px solid #f59e0b'
                        }}>
                          ⏳ Pendiente de Benchmark
                        </span>
                        <h3 style={{
                          margin: 0,
                          fontSize: '15px',
                          fontWeight: '700',
                          color: 'var(--text-primary)',
                          fontFamily: 'monospace',
                          wordBreak: 'break-word'
                        }}>
                          {b.model}
                        </h3>
                      </div>
                      <div style={{
                        textAlign: 'right',
                        padding: '6px 12px',
                        borderRadius: '12px',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        border: '1px solid rgba(245, 158, 11, 0.3)'
                      }}>
                        <div style={{ fontSize: '18px', fontWeight: '800', color: '#f59e0b' }}>--</div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Sin Evaluar</div>
                      </div>
                    </div>

                    <div style={{
                      fontSize: '12px',
                      color: 'var(--text-muted)',
                      marginTop: '12px',
                      fontStyle: 'italic',
                      lineHeight: '1.5'
                    }}>
                      "{b.user_review}"
                    </div>

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: '8px',
                      marginTop: '16px',
                      backgroundColor: 'var(--bg-tertiary)',
                      padding: '10px',
                      borderRadius: '10px',
                      textAlign: 'center'
                    }}>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Tamaño</div>
                        <div style={{ fontSize: '13px', fontWeight: '700', color: '#06b6d4' }}>{b.file_size_gb} GB</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Estado</div>
                        <div style={{ fontSize: '13px', fontWeight: '700', color: '#f59e0b' }}>Por Evaluar</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>CLI</div>
                        <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)' }}>ai-arena</div>
                      </div>
                    </div>
                  </div>

                  <div style={{
                    marginTop: '16px',
                    paddingTop: '12px',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Comando CLI:</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(`ai-arena --model ${b.id}`);
                        alert(`Comando copiado:\nai-arena --model ${b.id}`);
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '700',
                        border: '1px solid var(--border-subtle)',
                        backgroundColor: 'var(--bg-tertiary)',
                        color: 'var(--text-primary)',
                        cursor: 'pointer'
                      }}
                    >
                      📋 Copiar Comando
                    </button>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={b.id}
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '16px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}
              >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px' }}>
                  <div>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '3px 8px',
                      borderRadius: '999px',
                      display: 'inline-block',
                      marginBottom: '6px',
                      backgroundColor: b.badge_class === 'badge-gold' ? 'rgba(251, 191, 36, 0.15)' :
                                       b.badge_class === 'badge-emerald' ? 'rgba(16, 185, 129, 0.15)' :
                                       b.badge_class === 'badge-cyan' ? 'rgba(6, 182, 212, 0.15)' :
                                       'rgba(244, 63, 94, 0.15)',
                      color: b.badge_class === 'badge-gold' ? '#fbbf24' :
                             b.badge_class === 'badge-emerald' ? '#10b981' :
                             b.badge_class === 'badge-cyan' ? '#06b6d4' :
                             '#f43f5e',
                      border: '1px solid currentColor'
                    }}>
                      {b.user_rank}
                    </span>
                    <h3 style={{
                      margin: 0,
                      fontSize: '15px',
                      fontWeight: '700',
                      color: 'var(--text-primary)',
                      fontFamily: 'monospace',
                      wordBreak: 'break-word'
                    }}>
                      {b.model}
                    </h3>
                  </div>

                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: '22px', fontWeight: '800', color: '#10b981' }}>
                      {b.score}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Puntuación TDD
                    </div>
                  </div>
                </div>

                {/* Star Rating Bar */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '12px',
                  marginBottom: '6px',
                  padding: '7px 12px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(251, 191, 36, 0.06)',
                  border: '1px solid rgba(251, 191, 36, 0.18)'
                }}>
                  <div>
                    <div style={{ fontSize: '9px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px' }}>
                      Tu Calificación:
                    </div>
                    <StarRating
                      value={b.stars || 0}
                      onChange={(newStars) => handleRateModel(b.id, newStars, null, null)}
                    />
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRateModel(b.id, b.stars || 3, !b.playable, null);
                    }}
                    title="Haz click para alternar entre Jugable y Roto (evita falsos 100/100)"
                    style={{
                      background: b.playable ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                      border: `1px solid ${b.playable ? 'rgba(16, 185, 129, 0.4)' : 'rgba(244, 63, 94, 0.4)'}`,
                      borderRadius: '8px',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: b.playable ? '#10b981' : '#f43f5e',
                      fontSize: '11px',
                      fontWeight: '700'
                    }}
                  >
                    {b.playable ? (
                      <>
                        <CheckCircle2 size={13} />
                        <span>✓ Jugable</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle size={13} />
                        <span>❌ Roto</span>
                      </>
                    )}
                  </button>
                </div>

                {/* User review bubble with edit button */}
                <div style={{
                  backgroundColor: 'var(--bg-tertiary)',
                  borderLeft: `3px solid ${b.playable ? '#10b981' : '#f43f5e'}`,
                  borderRadius: '0 8px 8px 0',
                  padding: '9px 12px',
                  fontSize: '12px',
                  lineHeight: '1.45',
                  color: b.playable ? 'var(--text-secondary)' : '#fda4af',
                  fontStyle: 'italic',
                  margin: '8px 0 14px 0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '8px'
                }}>
                  <span style={{ flex: 1 }}>"{b.user_review}"</span>
                  <button
                    type="button"
                    onClick={() => {
                      const newRev = prompt('Tu opinión sobre este modelo (ej: 100/100 sintético pero no se mueve la serpiente):', b.user_review);
                      if (newRev !== null && newRev.trim()) {
                        handleRateModel(b.id, b.stars || 3, b.playable, newRev.trim());
                      }
                    }}
                    title="Editar tu opinión"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      padding: '2px',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <Edit3 size={13} />
                  </button>
                </div>

                {/* Metrics Row */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '8px',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '10px',
                  padding: '10px 12px',
                  fontSize: '11px',
                  fontFamily: 'monospace'
                }}>
                  <div>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Velocidad</div>
                    <div style={{ fontSize: '13px', fontWeight: '700', color: '#10b981', marginTop: '2px' }}>
                      {b.speed_tps > 0 ? `${b.speed_tps.toFixed(1)} t/s` : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tiempo</div>
                    <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                      {b.time_sec > 0 ? `${b.time_sec.toFixed(0)} s` : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tokens</div>
                    <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                      {b.tokens > 0 ? b.tokens.toLocaleString() : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '16px',
                paddingTop: '12px',
                borderTop: '1px solid var(--border-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {b.playable ? (
                    <span style={{ fontSize: '11px', fontWeight: '700', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle2 size={13} />
                      <span>100% Jugable</span>
                    </span>
                  ) : (
                    <span style={{ fontSize: '11px', fontWeight: '700', color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <AlertTriangle size={13} />
                      <span>Defectuoso</span>
                    </span>
                  )}
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({b.rating_str})</span>
                </div>

                <button
                  onClick={() => setActiveModalModel(b.model)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: '#10b981',
                    color: '#000',
                    fontWeight: '700',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'opacity 0.15s ease'
                  }}
                >
                  <Gamepad2 size={15} />
                  <span>Probar Juego</span>
                </button>
              </div>
            </div>
          );
        })}
        </div>
      ) : (
        /* Table View */
        <div style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '16px',
          overflowX: 'auto'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-tertiary)' }}>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Modelo</th>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Puntuación TDD</th>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Tus Estrellas & Veredicto</th>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Velocidad</th>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Tiempo</th>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Tokens</th>
                <th style={{ padding: '12px 18px', fontWeight: '700', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>Acción</th>
              </tr>
            </thead>
            <tbody>
              {filteredBenchmarks.map((b) => {
                if (b.status === 'pending') {
                  return (
                    <tr key={b.id} style={{ borderBottom: '1px solid var(--border-subtle)', opacity: 0.85 }}>
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ fontWeight: '700', fontFamily: 'monospace', color: 'var(--text-primary)' }}>{b.model}</div>
                        <div style={{ fontSize: '11px', color: '#f59e0b', marginTop: '2px' }}>{b.file_size_gb} GB &bull; Pendiente de benchmark</div>
                      </td>
                      <td style={{ padding: '14px 18px' }}>
                        <span style={{ fontSize: '16px', fontWeight: '800', color: '#f59e0b' }}>--</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}> / 100</span>
                      </td>
                      <td style={{ padding: '14px 18px' }}>
                        <span style={{
                          fontSize: '11px',
                          fontWeight: '700',
                          padding: '2px 8px',
                          borderRadius: '999px',
                          backgroundColor: 'rgba(245, 158, 11, 0.15)',
                          color: '#f59e0b',
                          border: '1px solid #f59e0b'
                        }}>
                          ⏳ Pendiente
                        </span>
                      </td>
                      <td style={{ padding: '14px 18px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>N/A</td>
                      <td style={{ padding: '14px 18px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>N/A</td>
                      <td style={{ padding: '14px 18px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>N/A</td>
                      <td style={{ padding: '14px 18px' }}>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(`ai-arena --model ${b.id}`);
                            alert(`Comando copiado:\nai-arena --model ${b.id}`);
                          }}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-subtle)',
                            backgroundColor: 'var(--bg-tertiary)',
                            color: 'var(--text-primary)',
                            fontSize: '11px',
                            cursor: 'pointer'
                          }}
                        >
                          📋 Comando
                        </button>
                      </td>
                    </tr>
                  );
                }

                return (
                  <tr key={b.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: '700', fontFamily: 'monospace', color: 'var(--text-primary)' }}>{b.model}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{b.user_review.substring(0, 60)}...</div>
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <span style={{ fontSize: '16px', fontWeight: '800', color: '#10b981' }}>{b.score}</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}> / 100</span>
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <StarRating
                        value={b.stars || 0}
                        onChange={(newStars) => handleRateModel(b.id, newStars, null, null)}
                      />
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{
                          fontSize: '10px',
                          fontWeight: '700',
                          padding: '2px 6px',
                          borderRadius: '999px',
                          backgroundColor: b.badge_class === 'badge-gold' ? 'rgba(251, 191, 36, 0.15)' :
                                           b.badge_class === 'badge-emerald' ? 'rgba(16, 185, 129, 0.15)' :
                                           b.badge_class === 'badge-cyan' ? 'rgba(6, 182, 212, 0.15)' :
                                           'rgba(244, 63, 94, 0.15)',
                          color: b.badge_class === 'badge-gold' ? '#fbbf24' :
                                 b.badge_class === 'badge-emerald' ? '#10b981' :
                                 b.badge_class === 'badge-cyan' ? '#06b6d4' :
                                 '#f43f5e',
                          border: '1px solid currentColor'
                        }}>
                          {b.user_rank}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRateModel(b.id, b.stars || 3, !b.playable, null)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '11px',
                            fontWeight: '700',
                            color: b.playable ? '#10b981' : '#f43f5e'
                          }}
                        >
                          {b.playable ? '✓ Jugable' : '❌ Roto'}
                        </button>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '14px 18px', color: '#10b981', fontFamily: 'monospace', fontWeight: '600' }}>
                    {b.speed_tps > 0 ? `${b.speed_tps.toFixed(1)} t/s` : 'N/A'}
                  </td>
                  <td style={{ padding: '14px 18px', fontFamily: 'monospace' }}>
                    {b.time_sec > 0 ? `${b.time_sec.toFixed(0)} s` : 'N/A'}
                  </td>
                  <td style={{ padding: '14px 18px', fontFamily: 'monospace' }}>
                    {b.tokens > 0 ? b.tokens.toLocaleString() : 'N/A'}
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <button
                      onClick={() => setActiveModalModel(b.model)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        backgroundColor: '#10b981',
                        color: '#000',
                        fontWeight: '700',
                        fontSize: '11px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Gamepad2 size={13} />
                      <span>Jugar</span>
                    </button>
                  </td>
                </tr>
              );
            })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Game Sandbox Player */}
      {activeModalModel && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '960px',
            height: '88vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '14px 20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'var(--bg-tertiary)',
              borderBottom: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Gamepad2 size={18} style={{ color: '#10b981' }} />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Arcade Sandbox:</span>
                <span style={{ fontSize: '14px', fontWeight: '700', fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                  {activeModalModel}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <a
                  href={`/api/benchmarks/${activeModalModel}/preview`}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    padding: '5px 10px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: '600',
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>Pestaña Nueva</span>
                  <ExternalLink size={12} />
                </a>

                <button
                  onClick={() => setActiveModalModel(null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex'
                  }}
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Embedded Iframe */}
            <iframe
              src={`/api/benchmarks/${activeModalModel}/preview`}
              style={{
                flex: 1,
                width: '100%',
                border: 'none',
                backgroundColor: '#000'
              }}
              title="Arcade Snake Preview"
            />
          </div>
        </div>
      )}
    </div>
  );
}
