import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div style={{ ...styles.wrapper, flexDirection: isUser ? 'row-reverse' : 'row' }}>
      {/* Avatar */}
      <div style={{ ...styles.avatar, background: isUser ? '#1d4ed8' : '#065f46' }}>
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Bubble */}
      <div
        style={{
          ...styles.bubble,
          background: isUser ? '#1e3a8a' : '#1e2130',
          borderColor: isUser ? '#3b82f6' : '#334155',
          maxWidth: isUser ? '70%' : '80%',
          alignSelf: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        {isUser ? (
          <p style={styles.userText}>{message.content}</p>
        ) : (
          <div style={styles.botText}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        {message.sources && message.sources.length > 0 && (
          <div style={styles.sources}>
            <span style={styles.sourceLabel}>Sources: </span>
            {message.sources.map((s, i) => (
              <span key={i} style={styles.sourceChip}>{s}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 16,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    color: '#fff',
    marginTop: 2,
  },
  bubble: {
    border: '1px solid',
    borderRadius: 14,
    padding: '10px 14px',
    lineHeight: 1.6,
  },
  userText: {
    fontSize: 14,
    color: '#e2e8f0',
  },
  botText: {
    fontSize: 14,
    color: '#cbd5e1',
    lineHeight: 1.7,
  },
  sources: {
    marginTop: 8,
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 4,
  },
  sourceLabel: {
    fontSize: 11,
    color: '#64748b',
  },
  sourceChip: {
    fontSize: 11,
    background: '#0f172a',
    color: '#7dd3fc',
    border: '1px solid #1e3a4c',
    borderRadius: 4,
    padding: '1px 6px',
  },
};
