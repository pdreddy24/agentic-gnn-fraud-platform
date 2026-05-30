import { useEffect, useState } from "react";
import { Download, RefreshCcw } from "lucide-react";
import { downloadCsv, getJson } from "../api/client.js";
import BatchTable from "../components/BatchTable.jsx";
import ResultsTable from "../components/ResultsTable.jsx";

export default function HistoryPage() {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState("");
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadHistory() {
    setLoading(true);
    setError("");

    try {
      const result = await getJson("/uploads/history?limit=50", true);
      setBatches(result.batches || []);
      if (!selectedBatch && result.batches?.length) {
        setSelectedBatch(String(result.batches[0].id));
      }
    } catch (err) {
      setError(err.message || "Could not load history");
    } finally {
      setLoading(false);
    }
  }

  async function loadPredictions(batchId = selectedBatch) {
    if (!batchId) return;

    setLoading(true);
    setError("");

    try {
      const result = await getJson(`/uploads/${batchId}/predictions?limit=1000`, true);
      setPredictions(result.predictions || []);
    } catch (err) {
      setError(err.message || "Could not load predictions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Previous Uploads</h1>
          <p>View stored upload batches and download previous prediction results.</p>
        </div>

        <button className="secondary-button" onClick={loadHistory}>
          <RefreshCcw size={17} />
          Refresh
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="card">
        <div className="section-title">
          <div>
            <h3>Upload History</h3>
            <p>{batches.length} batch records found.</p>
          </div>
        </div>

        <BatchTable batches={batches} />
      </div>

      <div className="card">
        <div className="section-title">
          <div>
            <h3>Load Stored Predictions</h3>
            <p>Select a batch and view saved row-level results.</p>
          </div>
        </div>

        <div className="inline-form">
          <select value={selectedBatch} onChange={(e) => setSelectedBatch(e.target.value)}>
            {batches.map((batch) => (
              <option key={batch.id} value={batch.id}>
                Batch {batch.id} — {batch.filename}
              </option>
            ))}
          </select>

          <button className="primary-button" onClick={() => loadPredictions()} disabled={loading}>
            {loading ? "Loading..." : "Load Predictions"}
          </button>

          {predictions.length > 0 && (
            <button
              className="secondary-button"
              onClick={() => downloadCsv(`stored_predictions_batch_${selectedBatch}.csv`, predictions)}
            >
              <Download size={17} />
              Download
            </button>
          )}
        </div>

        <ResultsTable rows={predictions} />
      </div>
    </section>
  );
}
