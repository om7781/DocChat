import { Upload, FileText, X } from 'lucide-react';
import { useRef } from 'react';

const ACCEPTED = '.pdf,.txt,.docx,.csv,.md';

export default function FileUploadZone({ onUpload, isUploading, uploadedFile, onClear }) {
  const inputRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) onUpload(file);
  };

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) onUpload(file);
  };

  if (uploadedFile) {
    return (
      <div style={styles.uploadedBadge}>
        <FileText size={16} color="#7dd3fc" />
        <span style={styles.fileName}>{uploadedFile}</span>
        <button style={styles.clearBtn} onClick={onClear} title="Remove file">
          <X size={14} />
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        ...styles.dropZone,
        opacity: isUploading ? 0.7 : 1,
        cursor: isUploading ? 'not-allowed' : 'pointer',
      }}
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      onClick={() => !isUploading && inputRef.current.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        style={{ display: 'none' }}
        onChange={handleChange}
        disabled={isUploading}
      />
      <Upload size={32} color="#7dd3fc" style={{ marginBottom: 12 }} />
      {isUploading ? (
        <p style={styles.dropText}>Processing your file...</p>
      ) : (
        <>
          <p style={styles.dropText}>Drop your file here or <span style={styles.link}>browse</span></p>
          <p style={styles.dropSub}>Supports PDF, TXT, DOCX, CSV, MD</p>
        </>
      )}
    </div>
  );
}

const styles = {
  dropZone: {
    border: '2px dashed #334155',
    borderRadius: 16,
    padding: '40px 24px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#1e2130',
    transition: 'border-color 0.2s',
    userSelect: 'none',
  },
  dropText: {
    fontSize: 15,
    color: '#94a3b8',
    marginBottom: 4,
  },
  dropSub: {
    fontSize: 12,
    color: '#475569',
  },
  link: {
    color: '#7dd3fc',
    textDecoration: 'underline',
  },
  uploadedBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: '#1e3a4c',
    border: '1px solid #0ea5e9',
    borderRadius: 8,
    padding: '8px 14px',
    marginBottom: 4,
  },
  fileName: {
    fontSize: 13,
    color: '#7dd3fc',
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: 220,
  },
  clearBtn: {
    background: 'none',
    border: 'none',
    color: '#94a3b8',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    padding: 2,
    borderRadius: 4,
  },
};
