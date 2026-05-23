import { useMemo } from 'react';
import { computeAllStats } from '../utils/stats';

const CARD_CONFIG = [
  {
    key: 'highRisk',
    label: 'High Risk Transactions',
    icon: '🚨',
    className: 'stat-card stat-card-high-risk',
    subtitle: 'risk_score ≥ 80',
  },
  {
    key: 'highFrequencyAccounts',
    label: 'High Frequency Accounts',
    icon: '⏱️',
    className: 'stat-card stat-card-velocity',
    subtitle: '≥ 3 txns in any 1-hour window',
  },
  {
    key: 'locationMismatches',
    label: 'Location Mismatches',
    icon: '📍',
    className: 'stat-card stat-card-location',
    subtitle: 'location_consistency = 0',
  },
];

export default function StatsCards({ transactions }) {
  const stats = useMemo(() => computeAllStats(transactions), [transactions]);

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      {CARD_CONFIG.map(({ key, label, icon, className, subtitle }) => (
        <div key={key} className={className}>
          <div className="text-sm text-zinc-400 mb-1">
            {icon} {label}
          </div>
          <div className="text-3xl font-bold text-white">{stats[key]}</div>
          <div className="text-xs text-zinc-500 mt-2">{subtitle}</div>
        </div>
      ))}
    </div>
  );
}
