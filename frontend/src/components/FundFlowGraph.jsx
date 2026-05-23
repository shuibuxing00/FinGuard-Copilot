import { useEffect, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { TRANSACTIONS } from '../data/transactions';

function buildGraphData(transactions) {
  const nodeMap = {};
  const edgeMap = {};

  for (const t of transactions) {
    const from = t.user_id;
    const to = t.counterparty_id || 'external';
    if (!nodeMap[from]) {
      nodeMap[from] = { riskScores: [], anomalyCount: 0 };
    }
    nodeMap[from].riskScores.push(t.risk_score);
    if (t.anomaly_type) nodeMap[from].anomalyCount += 1;

    if (!nodeMap[to]) {
      nodeMap[to] = { riskScores: [0], anomalyCount: 0 };
    }

    const key = `${from}->${to}`;
    if (!edgeMap[key]) {
      edgeMap[key] = { from, to, amount: 0, count: 0 };
    }
    edgeMap[key].amount += t.amount;
    edgeMap[key].count += 1;
  }

  const nodes = Object.entries(nodeMap).map(([id, meta]) => {
    const maxRisk = Math.max(...meta.riskScores);
    const isHigh = maxRisk >= 80;
    return {
      id,
      name: id,
      symbolSize: isHigh ? 42 : 28,
      itemStyle: { color: isHigh ? '#ef4444' : '#3b82f6' },
      maxRisk,
      anomalyCount: meta.anomalyCount,
    };
  });

  const links = Object.values(edgeMap).map((e) => ({
    source: e.from,
    target: e.to,
    value: e.amount,
    count: e.count,
    lineStyle: {
      width: Math.min(8, 1 + e.count * 0.8),
      curveness: 0.2,
    },
  }));

  return { nodes, links };
}

export default function FundFlowGraph({ transactions = TRANSACTIONS }) {
  const chartRef = useRef(null);
  const graph = useMemo(() => buildGraphData(transactions), [transactions]);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current, 'dark');

    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: 'Fund Flow Network',
        subtext: 'Red = high risk (≥80) · Blue = normal',
        left: 'center',
        textStyle: { color: '#e6edf3' },
        subtextStyle: { color: '#8b949e' },
      },
      tooltip: {
        trigger: 'item',
        formatter(params) {
          if (params.dataType === 'node') {
            const d = params.data;
            return [
              `<b>${d.name}</b>`,
              `Risk Score: ${d.maxRisk}`,
              `Anomaly Txns: ${d.anomalyCount}`,
            ].join('<br/>');
          }
          if (params.dataType === 'edge') {
            return [
              `${params.data.source} → ${params.data.target}`,
              `Amount: $${params.data.value?.toLocaleString()}`,
              `Count: ${params.data.count} transaction(s)`,
            ].join('<br/>');
          }
          return '';
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          label: { show: true, color: '#e6edf3', fontSize: 10 },
          force: { repulsion: 280, edgeLength: [80, 160] },
          data: graph.nodes,
          links: graph.links,
          emphasis: { focus: 'adjacency' },
        },
      ],
    });

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
    };
  }, [graph]);

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold mb-4">Fund Flow Graph (ECharts)</h2>
      <div
        ref={chartRef}
        className="w-full rounded-lg border border-border bg-surface"
        style={{ height: 480 }}
      />
    </section>
  );
}
