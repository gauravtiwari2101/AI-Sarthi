import { useState, useRef, useEffect, useMemo } from 'react';
import {
  Send,
  Plus,
  Search,
  Trash2,
  Edit2,
  Copy,
  Check,
  Download,
  Sparkles,
  MessageSquare
} from 'lucide-react';
import apiService, { type ChatResponse } from '../services/api';
import { pdfGenerator } from '../utils/pdfGenerator';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  data?: ChatResponse;
  timestamp: string;
}

interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  messages: Message[];
}

const STARTER_PROMPTS = [
  "What percentage of funding goes to maternal health?",
  "What is the maternal health budget for FY 2022–23?",
  "Compare maternal and child health funding.",
  "Recommend funding for Nanded based on available data."
];

const STORAGE_KEY = 'ai_sarthi_conversations_v2';

export default function ChatWorkspace() {
  // Load conversations from localStorage
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error('Failed to load conversations from localStorage', e);
    }
    const defaultConv: Conversation = {
      id: 'conv-default',
      title: 'Maternal & Child Health Inquiry',
      createdAt: new Date().toISOString(),
      messages: []
    };
    return [defaultConv];
  });

  const [activeConvId, setActiveConvId] = useState<string>(() => {
    return conversations[0]?.id || 'conv-default';
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState('');
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null);
  const [editingTitleText, setEditingTitleText] = useState('');
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const isNearBottomRef = useRef(true);

  // Sync to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch (e) {
      console.error('Failed to persist conversations', e);
    }
  }, [conversations]);

  const activeConversation = useMemo(() => {
    return conversations.find(c => c.id === activeConvId) || conversations[0];
  }, [conversations, activeConvId]);

  const messages = activeConversation?.messages || [];

  // Track if user has scrolled up
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    isNearBottomRef.current = scrollHeight - scrollTop - clientHeight < 120;
  };

  useEffect(() => {
    if (isNearBottomRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  // Create new chat
  const handleNewChat = () => {
    const newConv: Conversation = {
      id: `conv-${Date.now()}`,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      messages: []
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConvId(newConv.id);
    setInput('');
    if (inputRef.current) inputRef.current.focus();
  };

  // Delete conversation
  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;

    setConversations(prev => {
      const filtered = prev.filter(c => c.id !== id);
      if (filtered.length === 0) {
        const fresh: Conversation = {
          id: `conv-${Date.now()}`,
          title: 'New Conversation',
          createdAt: new Date().toISOString(),
          messages: []
        };
        setActiveConvId(fresh.id);
        return [fresh];
      }
      if (activeConvId === id) {
        setActiveConvId(filtered[0].id);
      }
      return filtered;
    });
  };

  // Start editing title
  const handleStartRename = (c: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTitleId(c.id);
    setEditingTitleText(c.title);
  };

  // Save renamed title
  const handleSaveRename = (id: string) => {
    if (editingTitleText.trim()) {
      setConversations(prev => prev.map(c => c.id === id ? { ...c, title: editingTitleText.trim() } : c));
    }
    setEditingTitleId(null);
  };

  // Send message
  const handleSend = async (overridePrompt?: string) => {
    const q = (overridePrompt || input).trim();
    if (!q || loading) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: q,
      timestamp: new Date().toISOString()
    };

    // Update conversation with user message & auto-generate title if first message
    setConversations(prev => prev.map(c => {
      if (c.id === activeConvId) {
        const isFirst = c.messages.length === 0;
        const newTitle = isFirst ? (q.length > 32 ? q.substring(0, 30) + '...' : q) : c.title;
        return {
          ...c,
          title: newTitle,
          messages: [...c.messages, userMsg]
        };
      }
      return c;
    }));

    setInput('');
    setLoading(true);
    isNearBottomRef.current = true;

    try {
      const resp = await apiService.chat(q);
      const data = resp.data;

      const assistantMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: data.answer,
        data,
        timestamp: new Date().toISOString()
      };

      setConversations(prev => prev.map(c => {
        if (c.id === activeConvId) {
          return { ...c, messages: [...c.messages, assistantMsg] };
        }
        return c;
      }));
    } catch (err: any) {
      const assistantMsg: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: `Error connecting to financial backend: ${err?.message || 'Server timeout'}. Please verify backend service on port 8000.`,
        timestamp: new Date().toISOString()
      };
      setConversations(prev => prev.map(c => {
        if (c.id === activeConvId) {
          return { ...c, messages: [...c.messages, assistantMsg] };
        }
        return c;
      }));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const filteredConversations = conversations.filter(c =>
    c.title.toLowerCase().includes(searchHistory.toLowerCase())
  );

  return (
    <div className="chat-workspace" id="chat-workspace">
      {/* ChatGPT-Style Conversation History Sidebar */}
      <aside className="chat-sidebar" id="chat-history-sidebar">
        <button className="chat-new-btn" onClick={handleNewChat} id="btn-new-chat">
          <Plus size={15} />
          New Conversation
        </button>

        {/* Search Conversations Input */}
        <div style={{ position: 'relative', marginTop: 4 }}>
          <Search size={13} style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchHistory}
            onChange={e => setSearchHistory(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 8px 6px 26px',
              fontSize: 11.5,
              borderRadius: 6,
              border: '1px solid var(--border-color)',
              background: '#FFFFFF',
              outline: 'none'
            }}
          />
        </div>

        {/* Conversations History List */}
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: 8 }}>
          Previous Discussions
        </div>

        <div className="chat-history-list">
          {filteredConversations.map(c => {
            const isActive = c.id === activeConvId;
            return (
              <div
                key={c.id}
                className={`chat-history-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveConvId(c.id)}
              >
                {editingTitleId === c.id ? (
                  <input
                    type="text"
                    value={editingTitleText}
                    onChange={e => setEditingTitleText(e.target.value)}
                    onBlur={() => handleSaveRename(c.id)}
                    onKeyDown={e => { if (e.key === 'Enter') handleSaveRename(c.id); }}
                    autoFocus
                    style={{ fontSize: 12, padding: '2px 4px', border: '1px solid var(--accent-teal)', width: '100%', borderRadius: 4 }}
                  />
                ) : (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                      <MessageSquare size={13} style={{ flexShrink: 0, opacity: isActive ? 1 : 0.6 }} />
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.title}</span>
                    </div>

                    <div style={{ display: 'flex', gap: 4, opacity: isActive ? 1 : 0, transition: 'opacity 0.15s' }}>
                      <button
                        onClick={e => handleStartRename(c, e)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}
                        title="Rename"
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        onClick={e => handleDeleteConversation(c.id, e)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--status-danger)', padding: 2 }}
                        title="Delete"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>

        <div style={{ marginTop: 'auto', paddingTop: 10, borderTop: '1px solid var(--border-color)', fontSize: 11, color: 'var(--text-muted)' }}>
          <div><strong>Model:</strong> Qwen3-4B LoRA</div>
          <div><strong>Hardware:</strong> Intel Arc 130V OpenVINO</div>
        </div>
      </aside>

      {/* Main Conversation Stream */}
      <div className="chat-main" id="chat-main-stream">
        <div
          className="chat-messages"
          id="chat-messages-container"
          ref={chatContainerRef}
          onScroll={handleScroll}
        >
          {/* Empty State with Starter Cards */}
          {messages.length === 0 && (
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
              padding: '40px 20px',
              textAlign: 'center',
            }}>
              <div className="navbar-logo" style={{ width: 44, height: 44, fontSize: 18 }}>MH</div>
              <h2 style={{ fontSize: 20, color: 'var(--primary-navy)' }}>
                Ask AI Sarthi Intelligence
              </h2>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 500, lineHeight: 1.6 }}>
                Official decision support assistant for the Maharashtra Public Health Department. Ask natural language questions regarding programme percentages, multi-year trends, district allocations, or citations.
              </p>

              {/* Starter Prompt Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, maxWidth: 600, width: '100%', marginTop: 12 }}>
                {STARTER_PROMPTS.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(p)}
                    style={{
                      background: '#FFFFFF',
                      border: '1px solid var(--border-color)',
                      borderRadius: 6,
                      padding: '10px 14px',
                      textAlign: 'left',
                      fontSize: 12.5,
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: 'var(--shadow-xs)'
                    }}
                    onMouseOver={e => {
                      (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent-teal)';
                      (e.currentTarget as HTMLElement).style.background = 'var(--accent-teal-subtle)';
                    }}
                    onMouseOut={e => {
                      (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-color)';
                      (e.currentTarget as HTMLElement).style.background = '#FFFFFF';
                    }}
                  >
                    <Sparkles size={12} color="var(--accent-teal)" style={{ marginBottom: 4 }} />
                    <div>{p}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages List */}
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-bubble">
                {/* Content */}
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>
                  {msg.content}
                </div>

                {/* Key Metrics Grid */}
                {msg.data?.key_metrics && (
                  <div className="key-metrics-grid">
                    {Array.isArray(msg.data.key_metrics)
                      ? msg.data.key_metrics.map((km: any, idx: number) => (
                          <div key={idx} className={`key-metric-card ${idx % 2 === 1 ? 'amber' : ''}`}>
                            <div className="key-metric-label">{km.label || km.name || 'Metric'}</div>
                            <div className="key-metric-val">{String(km.value)}</div>
                          </div>
                        ))
                      : Object.entries(msg.data.key_metrics).map(([key, val], idx) => (
                          <div key={idx} className={`key-metric-card ${idx % 2 === 1 ? 'amber' : ''}`}>
                            <div className="key-metric-label">{key.replace(/_/g, ' ')}</div>
                            <div className="key-metric-val">{String(val)}</div>
                          </div>
                        ))}
                  </div>
                )}

                {/* Structured Table */}
                {msg.data?.table_data && (
                  <div className="data-table-container" style={{ margin: '12px 0' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          {'headers' in msg.data.table_data && Array.isArray(msg.data.table_data.headers)
                            ? msg.data.table_data.headers.map((col: string, colIdx: number) => (
                                <th key={colIdx}>{col.replace(/_/g, ' ')}</th>
                              ))
                            : Array.isArray(msg.data.table_data) && msg.data.table_data.length > 0
                            ? Object.keys(msg.data.table_data[0]).map((col: string, colIdx: number) => (
                                <th key={colIdx}>{col.replace(/_/g, ' ')}</th>
                              ))
                            : null}
                        </tr>
                      </thead>
                      <tbody>
                        {'rows' in msg.data.table_data && Array.isArray(msg.data.table_data.rows)
                          ? msg.data.table_data.rows.map((row: any, rIdx: number) => (
                              <tr key={rIdx}>
                                {row.map((cellVal: any, cIdx: number) => (
                                  <td key={cIdx} className={typeof cellVal === 'number' || String(cellVal).includes('₹') || String(cellVal).includes('%') ? 'num' : ''}>
                                    {String(cellVal)}
                                  </td>
                                ))}
                              </tr>
                            ))
                          : Array.isArray(msg.data.table_data)
                          ? msg.data.table_data.map((row: any, rIdx: number) => (
                              <tr key={rIdx}>
                                {Object.values(row).map((cellVal: any, cIdx: number) => (
                                  <td key={cIdx} className={typeof cellVal === 'number' || String(cellVal).includes('₹') || String(cellVal).includes('%') ? 'num' : ''}>
                                    {String(cellVal)}
                                  </td>
                                ))}
                              </tr>
                            ))
                          : null}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Verified Citations Box (1-3 citations) */}
                {msg.data?.sources && msg.data.sources.length > 0 && (
                  <div className="citations-box">
                    <div className="citations-header">Verified Sources & Citations</div>
                    {msg.data.sources.slice(0, 3).map((src, sIdx) => (
                      <div key={sIdx} className="citation-item">
                        📄 {src}
                      </div>
                    ))}
                  </div>
                )}

                {/* Assistant Action Buttons: Copy & Export PDF */}
                {msg.role === 'assistant' && (
                  <div style={{ display: 'flex', gap: 8, marginTop: 12, paddingTop: 8, borderTop: '1px solid var(--border-color)' }}>
                    <button
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: 11, padding: '3px 8px' }}
                    >
                      {copiedMsgId === msg.id ? <Check size={12} color="var(--status-success)" /> : <Copy size={12} />}
                      {copiedMsgId === msg.id ? 'Copied' : 'Copy Text'}
                    </button>

                    <button
                      onClick={() => pdfGenerator.generateChatAnswerReport(
                        messages.find(m => m.id < msg.id && m.role === 'user')?.content || 'Executive Query',
                        msg.content,
                        msg.data?.key_metrics,
                        msg.data?.sources || []
                      )}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: 11, padding: '3px 8px' }}
                    >
                      <Download size={12} /> Export Briefing PDF
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div className="spinner" />
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  Synthesizing verified policy brief from reconciled database...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Composer Input Area */}
        <div className="chat-input-area" id="chat-composer-area">
          <div className="chat-input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask about maternal health funding, district allocations, or multi-year budget trends..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              id="chat-input-field"
            />
            <button
              className="chat-send-btn"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              id="chat-submit-btn"
              title="Send question"
            >
              <Send size={15} />
            </button>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
            Deterministic Financial Math • Official NHM PIP/ROP Records • Local OpenVINO Intel Arc Inference
          </div>
        </div>
      </div>
    </div>
  );
}
