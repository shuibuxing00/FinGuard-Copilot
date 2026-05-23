import { useState } from 'react';
import {
  buildCaseSummaries,
  formatCaseSummaryText,
  copyToClipboard,
  downloadTxt,
} from '../utils/exportCaseSummary';

export default function ExportCaseSummary({ transactions, threshold = 80 }) {
  const [status, setStatus] = useState('');

  const groups = buildCaseSummaries(transactions, threshold);
  const text = formatCaseSummaryText(groups);

  const handleCopy = async () => {
    try {
      await copyToClipboard(text);
      setStatus(`Copied ${groups.length} case(s) to clipboard.`);
    } catch {
      setStatus('Clipboard unavailable — use Download instead.');
    }
  };

  const handleDownload = () => {
    downloadTxt(text, `case-summary-${Date.now()}.txt`);
    setStatus(`Downloaded ${groups.length} case(s).`);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 mb-6 p-4 rounded-lg border border-border bg-surface">
      <button
        type="button"
        onClick={handleCopy}
        disabled={groups.length === 0}
        className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-sm font-medium"
      >
        Export Case Summary — Copy
      </button>
      <button
        type="button"
        onClick={handleDownload}
        disabled={groups.length === 0}
        className="px-4 py-2 rounded-lg border border-border bg-surface-light hover:bg-zinc-700 disabled:opacity-40 text-sm"
      >
        Download .txt
      </button>
      <span className="text-sm text-zinc-400">
        {groups.length} user(s) with risk_score ≥ {threshold}
      </span>
      {status && <span className="text-sm text-emerald-400">{status}</span>}
    </div>
  );
}
