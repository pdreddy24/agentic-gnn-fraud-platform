import DecisionBadge from "./DecisionBadge.jsx";

function formatValue(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") return Number(value).toFixed(4).replace(/\.0000$/, "");
  return String(value);
}

export default function ResultsTable({ rows = [] }) {
  if (!rows.length) {
    return <div className="empty-state">No prediction rows to show.</div>;
  }

  const preferredColumns = [
    "row_number",
    "transaction_id",
    "decision",
    "final_risk",
    "gnn_graph_score",
    "ml_score",
    "llm_summary",
  ];

  const columns = preferredColumns.filter((column) => Object.prototype.hasOwnProperty.call(rows[0], column));

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.transaction_id || row.id || index}-${index}`}>
              {columns.map((column) => (
                <td key={column}>
                  {column === "decision" ? <DecisionBadge decision={row[column]} /> : formatValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
