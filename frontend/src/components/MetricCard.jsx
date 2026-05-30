export default function MetricCard({ icon: Icon, label, value, hint }) {
  return (
    <div className="metric-card">
      <div>
        <p>{label}</p>
        <h3>{value}</h3>
        {hint && <span>{hint}</span>}
      </div>

      {Icon && (
        <div className="metric-icon">
          <Icon size={22} />
        </div>
      )}
    </div>
  );
}
