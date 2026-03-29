import { useState } from 'react';

export default function UploadPanel({ onAnalyzeText, onAnalyzeUpload, onLoadSample, onLoadSimpleInboundSample, loading, docMeta }) {
  const [draftText, setDraftText] = useState('');
  const [draftFileName, setDraftFileName] = useState('pasted_contract.txt');
  const [selectedFile, setSelectedFile] = useState(null);

  const submitText = () => {
    if (!draftText.trim()) return;
    onAnalyzeText({ text: draftText, fileName: draftFileName || 'pasted_contract.txt' });
  };

  const submitFile = () => {
    if (!selectedFile) return;
    onAnalyzeUpload(selectedFile);
  };

  return (
    <section className="panel stack gap-sm">
      <div className="panel-header panel-header-wrap">
        <div>
          <h3>Ingest contract</h3>
          <p>Upload a file, paste text, or load one of the bundled samples.</p>
        </div>
        <div className="inline-actions">
          <button className="button ghost" type="button" onClick={onLoadSample} disabled={loading}>
            Load review sample
          </button>
          <button className="button ghost" type="button" onClick={onLoadSimpleInboundSample} disabled={loading}>
            Load simple inbound
          </button>
        </div>
      </div>

      <div className="stack gap-xs">
        <label className="field">
          <span>Upload PDF, DOCX, TXT, or image</span>
          <input type="file" accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.tif,.tiff,.bmp,.webp" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
        </label>
        <button className="button" type="button" onClick={submitFile} disabled={loading || !selectedFile}>
          Analyze uploaded file
        </button>
      </div>

      <div className="divider" />

      <label className="field">
        <span>File name for pasted text</span>
        <input value={draftFileName} onChange={(e) => setDraftFileName(e.target.value)} placeholder="contract.txt" />
      </label>
      <label className="field">
        <span>Paste contract text</span>
        <textarea
          value={draftText}
          onChange={(e) => setDraftText(e.target.value)}
          placeholder="Paste a contract, order form, or section excerpt here..."
          rows={12}
        />
      </label>
      <button className="button" type="button" onClick={submitText} disabled={loading || !draftText.trim()}>
        Analyze pasted text
      </button>

      {docMeta ? (
        <div className="soft-box stack gap-xs">
          <strong>Current document</strong>
          <span>{docMeta.file_name}</span>
          <span className="muted">{docMeta.contract_type} • {docMeta.page_count} pages • {docMeta.section_count} sections</span>
          {docMeta.notes?.ocr_status ? <span className="warning-inline">{docMeta.notes.ocr_status}</span> : null}
        </div>
      ) : (
        <div className="soft-box muted">No contract loaded yet.</div>
      )}
    </section>
  );
}
