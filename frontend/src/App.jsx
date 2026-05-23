import { useState } from 'react';
import { TRANSACTIONS } from './data/transactions';
import StatsCards from './components/StatsCards';
import ExportCaseSummary from './components/ExportCaseSummary';
import RoleTransactionTable from './components/RoleTransactionTable';
import AmlRulesPanel from './components/AmlRulesPanel';
import FundFlowGraph from './components/FundFlowGraph';

export default function App() {
  const [role, setRole] = useState('analyst');
  const [transactions] = useState(TRANSACTIONS);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-white">FinGuard Compliance Dashboard</h1>
        <p className="text-zinc-500 mt-1">
          Mock frontend — synthetic data, RBAC table, AML rules, fund flow, export
        </p>
      </header>

      <StatsCards transactions={transactions} />
      <ExportCaseSummary transactions={transactions} />
      <AmlRulesPanel />
      <RoleTransactionTable
        transactions={transactions}
        role={role}
        onRoleChange={setRole}
      />
      <FundFlowGraph transactions={transactions} />

      <footer className="text-xs text-zinc-600 pt-8 border-t border-border">
        Data: frontend/mock/transactions.json (30 records, 20% high risk)
      </footer>
    </div>
  );
}
