import { BarChart, Bar, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import MetricCard from "./MetricCard.jsx";

export default function ComparePanel({ comparison }) {
  if (!comparison) {
    return (
      <div className="card muted-card">
        <h3>Comparison</h3>
        <p>No previous upload comparison available yet. Upload at least two CSV files to compare trends.</p>
      </div>
    );
  }

  const comp = comparison.comparison || {};
  const current = comparison.current_batch || {};
  const previous = comparison.previous_batch || {};

  const chartData = [
    { name: "Average Risk", Current: Number(current.average_risk || 0), Previous: Number(previous.average_risk || 0) },
    { name: "Review", Current: Number(current.review_count || 0), Previous: Number(previous.review_count || 0) },
    { name: "Blocked", Current: Number(current.block_count || 0), Previous: Number(previous.block_count || 0) },
    { name: "Approved", Current: Number(current.approve_count || 0), Previous: Number(previous.approve_count || 0) },
  ];

  return (
    <div className="card">
      <div className="section-title">
        <div>
          <h3>Comparison with Previous Upload</h3>
          <p>Current batch #{current.id} compared with previous batch #{previous.id}.</p>
        </div>
      </div>

      <div className="metrics-grid">
        <MetricCard label="Risk Change" value={comp.average_risk_change} hint={`${comp.average_risk_change_percent || 0}%`} />
        <MetricCard label="Review Change" value={comp.review_count_change} />
        <MetricCard label="Block Change" value={comp.block_count_change} />
        <MetricCard label="Approve Change" value={comp.approve_count_change} />
      </div>

      <div className="chart-box">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="Current" fill="#2563eb" radius={[8, 8, 0, 0]} />
            <Bar dataKey="Previous" fill="#94a3b8" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
