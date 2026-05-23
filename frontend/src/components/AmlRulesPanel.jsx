import { AML_RULES } from '../data/transactions';

/**
 * Explainable AML rules — analyst-facing read-only table.
 */
export default function AmlRulesPanel() {
  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold mb-2">AML Rules (Analyst View)</h2>
      <p className="text-sm text-zinc-500 mb-4">
        Read-only rule catalog for analysts. Hover a row to see which transactions match
        (velocity, device, location, amount rules). Auditors can edit rules in production.
      </p>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-surface-light text-zinc-400 text-xs uppercase">
            <tr>
              <th className="px-3 py-3 text-left">Rule Name</th>
              <th className="px-3 py-3 text-left">Condition</th>
              <th className="px-3 py-3 text-left">Action on Trigger</th>
            </tr>
          </thead>
          <tbody>
            {AML_RULES.map((rule) => (
              <tr
                key={rule.id}
                className="border-t border-border hover:bg-amber-950/20 transition-colors"
                title={`Rule ${rule.id}`}
              >
                <td className="px-3 py-2 font-medium text-amber-200/90">{rule.name}</td>
                <td className="px-3 py-2 font-mono text-xs text-zinc-400">{rule.condition}</td>
                <td className="px-3 py-2 text-zinc-300">{rule.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-4 rounded-lg bg-surface border border-border text-sm text-zinc-400">
        <strong className="text-zinc-200">Frontend display for analyst role:</strong>
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Place this panel above the transaction table (collapsed by default).</li>
          <li>Show only Rule Name, Condition (plain English), and Action columns.</li>
          <li>Hide internal rule IDs and backend SQL from analyst view.</li>
          <li>On row hover, highlight matching rows in the table (amber outline).</li>
          <li>Use amber badges for velocity rules, red for location, blue for device.</li>
        </ul>
      </div>
    </section>
  );
}
