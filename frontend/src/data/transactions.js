import raw from '../../mock/transactions.json';

export const TRANSACTIONS = raw;

export const AML_RULES = [
  {
    id: 'R001',
    name: 'High-Frequency Burst',
    condition: 'time_velocity >= 3 AND amount > 500',
    action: 'Increase risk_score +25; anomaly_type = short_time_high_freq; alert review',
  },
  {
    id: 'R002',
    name: 'New Device High Value',
    condition: 'device_new = true AND amount >= 3000',
    action: 'anomaly_type = new_device; risk_score +30; alert review',
  },
  {
    id: 'R003',
    name: 'Location Mismatch',
    condition: 'location_consistency = 0',
    action: 'anomaly_type = location_mismatch; risk_score +20; geo review',
  },
  {
    id: 'R004',
    name: 'Amount Peak Outlier',
    condition: 'amount > user_p95_baseline * 5',
    action: 'anomaly_type = amount_peak; risk_score +15; enhanced due diligence',
  },
  {
    id: 'R005',
    name: 'Compound Risk Escalation',
    condition: 'time_velocity >= 3 AND location_consistency = 0',
    action: 'Force risk_score >= 80; immediate auditor alert',
  },
];
