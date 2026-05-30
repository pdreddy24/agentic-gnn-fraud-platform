import { useMemo, useState } from "react";
import { Download, FileSpreadsheet, UploadCloud } from "lucide-react";
import { downloadCsv, uploadCsv } from "../api/client.js";
import MetricCard from "../components/MetricCard.jsx";
import ResultsTable from "../components/ResultsTable.jsx";
import ComparePanel from "../components/ComparePanel.jsx";

export default function Upload({ lastUploadResult, setLastUploadResult }) {
  const [file, setFile] = useState(null);
  const [useLlmForApproved, setUseLlmForApproved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const summary = lastUploadResult?.summary;
  const fileName = useMemo(() => file?.name || "No file selected", [file]);

  async function handleUpload() {
    if (!file) return;

    setLoading(true);
    setError("");

    try {
      const result = await uploadCsv(file, useLlmForApproved);
      setLastUploadResult(result);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Upload CSV and Predict</h1>
          <p>Upload transaction data and predict fraud risk for every row.</p>
        </div>
      </div>

      <div className="upload-layout">
        <div className="card upload-card">
          <div className="upload-icon">
            <UploadCloud size={34} />
          </div>

          <h3>Upload Transaction CSV</h3>
          <p>
            Required columns: transaction_id, user_id, device_id, card_id, ip_address,
            merchant_id, amount, timestamp, channel, country.
          </p>

          <label className="file-picker">
            <input type="file" accept=".csv" onChange={(event) => setFile(event.target.files?.[0] || null)} />
            <FileSpreadsheet size={20} />
            <span>{fileName}</span>
          </label>

          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={useLlmForApproved}
              onChange={(event) => setUseLlmForApproved(event.target.checked)}
            />
            Use LLM explanation for approved rows too
          </label>

          <div className="hint-box">
            Keep this checkbox off for large files. The model still predicts every row, but
            skips expensive LLM explanations for low-risk approved rows.
          </div>

          {error && <div className="error-box">{error}</div>}

          <button className="primary-button full" onClick={handleUpload} disabled={!file || loading}>
            {loading ? "Scoring file..." : "Upload and Predict"}
          </button>
        </div>

        <div className="card">
          <h3>CSV Example</h3>
          <pre className="csv-example">{`transaction_id,user_id,device_id,card_id,ip_address,merchant_id,amount,timestamp,channel,country
TBULK001,U0001,D0001,C0001,IP0001,M0001,9000,2026-05-29T03:00:01.189Z,web,NG
TBULK002,U0002,D0002,C0002,IP0002,M0002,250,2026-05-29T04:00:01.189Z,mobile,US`}</pre>
        </div>
      </div>

      {summary && (
        <>
          <div className="metrics-grid">
            <MetricCard label="Average Risk" value={summary.average_risk} />
            <MetricCard label="Approved" value={summary.approve_count} />
            <MetricCard label="Review" value={summary.review_count} />
            <MetricCard label="Blocked" value={summary.block_count} />
          </div>

          <ComparePanel comparison={lastUploadResult.comparison_with_previous_upload} />

          <div className="card">
            <div className="section-title">
              <div>
                <h3>Prediction Results</h3>
                <p>Batch ID: {lastUploadResult.batch_id}</p>
              </div>

              <button
                className="secondary-button"
                onClick={() =>
                  downloadCsv(`fraud_predictions_batch_${lastUploadResult.batch_id}.csv`, lastUploadResult.results || [])
                }
              >
                <Download size={17} />
                Download CSV
              </button>
            </div>

            <ResultsTable rows={lastUploadResult.results || []} />

            {lastUploadResult.failed_rows?.length > 0 && (
              <details className="details">
                <summary>Failed rows ({lastUploadResult.failed_rows.length})</summary>
                <pre>{JSON.stringify(lastUploadResult.failed_rows, null, 2)}</pre>
              </details>
            )}
          </div>
        </>
      )}
    </section>
  );
}
