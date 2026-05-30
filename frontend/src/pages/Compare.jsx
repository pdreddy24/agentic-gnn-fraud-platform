import { useEffect, useState } from "react";
import { RefreshCcw } from "lucide-react";
import { getJson } from "../api/client.js";
import ComparePanel from "../components/ComparePanel.jsx";

export default function Compare() {
  const [batches, setBatches] = useState([]);
  const [currentBatch, setCurrentBatch] = useState("");
  const [previousBatch, setPreviousBatch] = useState("");
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState("");

  async function loadHistory() {
    setError("");

    try {
      const result = await getJson("/uploads/history?limit=50", true);
      const rows = result.batches || [];
      setBatches(rows);

      if (rows.length >= 2) {
        setCurrentBatch(String(rows[0].id));
        setPreviousBatch(String(rows[1].id));
      }
    } catch (err) {
      setError(err.message || "Could not load batches");
    }
  }

  async function compare() {
    setError("");
    setComparison(null);

    if (!currentBatch || !previousBatch) {
      setError("Select two batches first.");
      return;
    }

    if (currentBatch === previousBatch) {
      setError("Select two different batches.");
      return;
    }

    try {
      const result = await getJson(`/uploads/compare/${currentBatch}/${previousBatch}`, true);
      setComparison(result);
    } catch (err) {
      setError(err.message || "Comparison failed");
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Compare Uploads</h1>
          <p>Compare average risk, review cases, blocked cases, and approved counts.</p>
        </div>

        <button className="secondary-button" onClick={loadHistory}>
          <RefreshCcw size={17} />
          Refresh
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="card">
        <div className="compare-select-grid">
          <div>
            <label>Current Batch</label>
            <select value={currentBatch} onChange={(e) => setCurrentBatch(e.target.value)}>
              {batches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  Batch {batch.id} — {batch.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label>Previous Batch</label>
            <select value={previousBatch} onChange={(e) => setPreviousBatch(e.target.value)}>
              {batches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  Batch {batch.id} — {batch.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button className="primary-button" onClick={compare}>
          Compare Uploads
        </button>
      </div>

      <ComparePanel comparison={comparison} />
    </section>
  );
}
