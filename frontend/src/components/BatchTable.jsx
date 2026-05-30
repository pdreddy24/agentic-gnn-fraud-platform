import DecisionBadge from "./DecisionBadge.jsx";

export default function BatchTable({ batches = [], compact = false }) {
  if (!batches.length) {
    return <div className="empty-state">No uploads yet.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Batch</th>
            <th>File</th>
            <th>Rows</th>
            <th>Avg Risk</th>
            <th>Approve</th>
            <th>Review</th>
            <th>Block</th>
            {!compact && <th>Created</th>}
          </tr>
        </thead>

        <tbody>
          {batches.map((batch) => (
            <tr key={batch.id}>
              <td>#{batch.id}</td>
              <td>{batch.filename}</td>
              <td>{batch.successful_rows}</td>
              <td>{Number(batch.average_risk || 0).toFixed(4)}</td>
              <td><DecisionBadge decision={`APPROVE ${batch.approve_count}`} /></td>
              <td><DecisionBadge decision={`REVIEW ${batch.review_count}`} /></td>
              <td><DecisionBadge decision={`BLOCK ${batch.block_count}`} /></td>
              {!compact && <td>{batch.created_at}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
