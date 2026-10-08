import { Send } from 'lucide-react';
import { useRef } from 'react';

export default function ChatInput({ onSend, disabled }) {
  const ref = useRef();

  const submit = () => {
    const val = ref.current.value.trim();
    if (!val || disabled) return;
    onSend(val);
    ref.current.value = '';
    ref.current.style.height = 'auto';
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const autoResize = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  return (
    <div style={styles.container}>
      <textarea
        ref={ref}
        rows={1}
        placeholder={disabled ? 'Upload a document to start chatting…' : 'Ask a question about your document…'}
        style={styles.input}
        onKeyDown={onKeyDown}
        onInput={autoResize}
        disabled={disabled}
      />
      <button
        style={{ ...styles.sendBtn, opacity: disabled ? 0.4 : 1 }}
        onClick={submit}
        disabled={disabled}
        title="Send (Enter)"
      >
        <Send size={18} />
      </button>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: 10,
    background: '#1e2130',
    border: '1px solid #334155',
    borderRadius: 14,
    padding: '8px 12px',
  },
  input: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#e2e8f0',
    fontSize: 14,
    resize: 'none',
    lineHeight: 1.6,
    fontFamily: 'inherit',
    overflowY: 'hidden',
  },
  sendBtn: {
    background: '#2563eb',
    border: 'none',
    borderRadius: 8,
    color: '#fff',
    width: 36,
    height: 36,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    flexShrink: 0,
    transition: 'background 0.2s',
  },
};
