const COLUMNS = [
  { key: 'amount', label: 'Amount', minRole: 'analyst' },
  { key: 'anomaly_type', label: 'Anomaly Type', minRole: 'analyst' },
  { key: 'risk_score', label: 'Risk Score', minRole: 'analyst' },
  { key: 'timestamp', label: 'Timestamp', minRole: 'analyst' },
  { key: 'user_id', label: 'User ID', minRole: 'analyst' },
  { key: 'device_id', label: 'Device ID', minRole: 'auditor' },
  { key: 'location', label: 'Location', minRole: 'auditor' },
];

const ROLE_LEVEL = { analyst: 1, auditor: 2, admin: 3 };

function canViewColumn(role, minRole) {
  return ROLE_LEVEL[role] >= ROLE_LEVEL[minRole];
}

function requiredRoleLabel(minRole) {
  const labels = {
    analyst: 'Analyst',
    auditor: 'Auditor',
    admin: 'Admin',
  };
  return labels[minRole] || minRole;
}

function LockedCell({ minRole }) {
  return (
    <td className="locked-cell relative px-3 py-2 text-center group">
      <span className="inline-flex items-center gap-1">
        <span aria-hidden>🔒</span>
        <span className="sr-only">Locked</span>
      </span>
      <span
        className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-full mb-1
          hidden group-hover:block z-20 whitespace-nowrap rounded bg-zinc-900 border border-border
          px-2 py-1 text-xs text-zinc-200 shadow-lg"
        role="tooltip"
      >
        Requires {requiredRoleLabel(minRole)} role
      </span>
    </td>
  );
}

function formatCell(key, value) {
  if (key === 'amount') return `$${Number(value).toLocaleString()}`;
  if (key === 'anomaly_type') return value || '—';
  if (key === 'timestamp') return value?.replace('T', ' ').replace('Z', '') ?? '—';
  return value ?? '—';
}

export default function RoleTransactionTable({ transactions, role, onRoleChange }) {
  const roles = ['analyst', 'auditor', 'admin'];

  const riskClass = (score) => {
    if (score >= 80) return 'text-red-400 font-semibold';
    if (score >= 50) return 'text-amber-400';
    return 'text-zinc-300';
  };

  return (
    <section className="mb-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <h2 className="text-lg font-semibold">Transaction Data (RBAC Table)</h2>
        <div className="flex gap-2">
          {roles.map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => onRoleChange(r)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                role === r
                  ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                  : 'bg-surface-light border border-border text-zinc-400 hover:text-white'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <p className="text-sm text-zinc-500 mb-3">
        Active role: <strong className="text-zinc-200 capitalize">{role}</strong> — locked
        columns show gray background with 🔒; hover for required role.
      </p>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-light text-zinc-400 uppercase text-xs">
            <tr>
              {COLUMNS.map((col) => {
                const visible = canViewColumn(role, col.minRole);
                return (
                  <th
                    key={col.key}
                    className={`px-3 py-3 ${!visible ? 'bg-zinc-800/50 text-zinc-600' : ''}`}
                  >
                    {col.label}
                    {!visible && ' 🔒'}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {transactions.map((row) => (
              <tr
                key={row.transaction_id}
                className={`border-t border-border hover:bg-surface-light/50 ${
                  row.risk_score >= 80 ? 'bg-red-950/20' : ''
                }`}
              >
                {COLUMNS.map((col) => {
                  if (!canViewColumn(role, col.minRole)) {
                    return <LockedCell key={col.key} minRole={col.minRole} />;
                  }
                  const val = row[col.key];
                  return (
                    <td
                      key={col.key}
                      className={`px-3 py-2 ${
                        col.key === 'risk_score' ? riskClass(row.risk_score) : ''
                      }`}
                    >
                      {formatCell(col.key, val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
