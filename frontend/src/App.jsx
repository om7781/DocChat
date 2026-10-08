import { useState, useRef, useEffect } from 'react';
import { Loader2, MessageSquare } from 'lucide-react';
import FileUploadZone from './components/FileUploadZone';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import { uploadFile, sendMessage, clearSession } from './api';
import './index.css';

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const bottomRef = useRef();

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleUpload = async (file) => {
    setIsUploading(true);
    setError(null);
    try {
      const { data } = await uploadFile(file);
      setSessionId(data.session_id);
      setUploadedFile(data.filename);
      setMessages([
        {
          role: 'bot',
          content: `✅ **${data.filename}** has been uploaded and processed! Ask me anything about it.`,
        },
      ]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClear = async () => {
    if (sessionId) {
      await clearSession(sessionId).catch(() => {});
    }
    setSessionId(null);
    setUploadedFile(null);
    setMessages([]);
    setError(null);
  };

  const handleSend = async (question) => {
    if (!sessionId) return;
    setError(null);

    // Append user message
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setIsThinking(true);

    try {
      const { data } = await sendMessage(sessionId, question);
      setMessages((prev) => [
        ...prev,
        { role: 'bot', content: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: `⚠️ ${err.response?.data?.detail || 'Something went wrong. Please try again.'}`,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div style={styles.layout}>
      {/* ── Sidebar ── */}
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <MessageSquare size={22} color="#7dd3fc" />
          <span style={styles.logoText}>DocChat</span>
        </div>

        <p style={styles.sidebarLabel}>DOCUMENT</p>
        <FileUploadZone
          onUpload={handleUpload}
          isUploading={isUploading}
          uploadedFile={uploadedFile}
          onClear={handleClear}
        />

        {isUploading && (
          <div style={styles.processingHint}>
            <Loader2 size={14} style={styles.spin} />
            <span>Embedding document…</span>
          </div>
        )}

        <div style={styles.infoBox}>
          <p style={styles.infoTitle}>How it works</p>
          <ol style={styles.infoList}>
            <li>Upload a document (PDF, DOCX, TXT, CSV, MD)</li>
            <li>The document is split and embedded using AI</li>
            <li>Ask questions — answers are grounded in the document</li>
          </ol>
        </div>

        <div style={styles.footer}>
          <span>Powered by</span>
          <span style={{ color: '#7dd3fc' }}> HuggingFace + LangChain</span>
        </div>
      </aside>

      {/* ── Main Chat ── */}
      <main style={styles.main}>
        {/* Header */}
        <div style={styles.header}>
          <h1 style={styles.headerTitle}>
            {uploadedFile ? `Chat — ${uploadedFile}` : 'DocChat'}
          </h1>
          {uploadedFile && (
            <span style={styles.headerBadge}>Document loaded</span>
          )}
        </div>

        {/* Messages */}
        <div style={styles.messages}>
          {messages.length === 0 && !isUploading && (
            <div style={styles.emptyState}>
              <MessageSquare size={48} color="#334155" />
              <p style={styles.emptyTitle}>No document uploaded yet</p>
              <p style={styles.emptySubtitle}>
                Upload a file from the sidebar to start a conversation
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <ChatMessage key={i} message={m} />
          ))}

          {isThinking && (
            <div style={styles.thinking}>
              <Loader2 size={16} style={styles.spin} color="#7dd3fc" />
              <span style={{ color: '#64748b', fontSize: 13 }}>Thinking…</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Error Banner */}
        {error && (
          <div style={styles.errorBanner}>
            ⚠️ {error}
          </div>
        )}

        {/* Input */}
        <div style={styles.inputArea}>
          <ChatInput onSend={handleSend} disabled={!sessionId || isThinking} />
          <p style={styles.hint}>Press Enter to send · Shift+Enter for newline</p>
        </div>
      </main>
    </div>
  );
}

const styles = {
  layout: {
    display: 'flex',
    height: '100vh',
    background: '#0f1117',
    overflow: 'hidden',
  },
  // ── Sidebar
  sidebar: {
    width: 300,
    minWidth: 260,
    background: '#13151f',
    borderRight: '1px solid #1e2533',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 18px',
    gap: 16,
    overflowY: 'auto',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  logoText: {
    fontSize: 20,
    fontWeight: 700,
    color: '#f1f5f9',
    letterSpacing: '-0.5px',
  },
  sidebarLabel: {
    fontSize: 10,
    fontWeight: 600,
    color: '#475569',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
  },
  processingHint: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    color: '#7dd3fc',
  },
  spin: {
    animation: 'spin 1s linear infinite',
  },
  infoBox: {
    background: '#1a1d2e',
    border: '1px solid #252a3d',
    borderRadius: 10,
    padding: '12px 14px',
    marginTop: 8,
  },
  infoTitle: {
    fontSize: 12,
    fontWeight: 600,
    color: '#94a3b8',
    marginBottom: 8,
  },
  infoList: {
    fontSize: 11,
    color: '#64748b',
    paddingLeft: 14,
    lineHeight: 1.8,
  },
  footer: {
    marginTop: 'auto',
    fontSize: 11,
    color: '#475569',
    textAlign: 'center',
  },
  // ── Main
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '16px 24px',
    borderBottom: '1px solid #1e2533',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    background: '#13151f',
    flexShrink: 0,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 600,
    color: '#f1f5f9',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  headerBadge: {
    fontSize: 11,
    background: '#052e16',
    color: '#4ade80',
    border: '1px solid #16a34a',
    borderRadius: 20,
    padding: '2px 10px',
    flexShrink: 0,
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    color: '#334155',
    textAlign: 'center',
    height: '100%',
    marginTop: '20%',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 600,
    color: '#475569',
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#334155',
    maxWidth: 300,
  },
  thinking: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 0',
  },
  errorBanner: {
    background: '#450a0a',
    border: '1px solid #991b1b',
    color: '#fca5a5',
    padding: '10px 20px',
    fontSize: 13,
    flexShrink: 0,
  },
  inputArea: {
    padding: '16px 24px',
    borderTop: '1px solid #1e2533',
    background: '#13151f',
    flexShrink: 0,
  },
  hint: {
    fontSize: 11,
    color: '#334155',
    marginTop: 6,
    textAlign: 'right',
  },
};
