export default function DecisionBadge({ decision }) {
  const value = String(decision || "UNKNOWN").toUpperCase();

  let className = "badge neutral";
  if (value.includes("APPROVE")) className = "badge approve";
  if (value.includes("REVIEW")) className = "badge review";
  if (value.includes("BLOCK")) className = "badge block";

  return <span className={className}>{value}</span>;
}
