/**
 * Export suspicious case summaries (risk_score >= threshold).
 */

export function buildCaseSummaries(transactions, threshold = 80) {
  const highRisk = transactions.filter((t) => t.risk_score >= threshold);
  const byUser = {};

  for (const t of highRisk) {
    if (!byUser[t.user_id]) {
      byUser[t.user_id] = {
        user_id: t.user_id,
        maxRisk: t.risk_score,
        behaviors: new Set(),
        totalAmount: 0,
        txnCount: 0,
      };
    }
    const g = byUser[t.user_id];
    g.maxRisk = Math.max(g.maxRisk, t.risk_score);
    g.totalAmount += t.amount;
    g.txnCount += 1;
    if (t.anomaly_type) g.behaviors.add(t.anomaly_type);
    if (t.risk_explanation) g.behaviors.add(t.risk_explanation);
  }

  return Object.values(byUser);
}

export function formatCaseSummaryText(groups) {
  const exportTime = new Date().toISOString().replace('T', ' ').slice(0, 19);
  const blocks = groups.map((g) => {
    const behavior = [...g.behaviors].join('; ') || 'High risk score cluster';
    return `---
Case Summary - Export Time: ${exportTime}
User ID: ${g.user_id}
Risk Score: ${g.maxRisk}
Suspicious Behavior: ${behavior}
Total Amount: ${g.totalAmount.toLocaleString('en-US', { maximumFractionDigits: 2 })}
Transaction Count: ${g.txnCount}
---`;
  });
  return blocks.join('\n\n');
}

export async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text);
}

export function downloadTxt(text, filename = 'case-summary.txt') {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
