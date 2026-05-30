import { useState } from "react";
import { Download, FileUp, Loader2, Sparkles } from "lucide-react";
import { downloadCsv, uploadCsv } from "../api/client.js";
import ResultsTable from "../components/ResultsTable.jsx";

export default function Upload({
  lastUploadResult,
  setLastUploadResult,
  goToPage,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [useLlmForAllRows, setUseLlmForAllRows] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const result = lastUploadResult;

  function handleFileChange(event) {
    const file = event.target.files?.[0];

    setError("");
    setSelectedFile(file || null);
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile) {
      setError("Please select a CSV file first.");
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Only CSV files are allowed.");
      return;
    }

    setUploading(true);
    setError("");

    try {
      /*
        IMPORTANT:
        true  = use LLM explanation for APPROVED rows also
        false = skip LLM for approved rows to make batch faster
      */
      const uploadResult = await uploadCsv(selectedFile, useLlmForAllRows);

      setLastUploadResult(uploadResult);
    } catch (err) {
      setError(err.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDownload() {
    if (!result?.download_url) {
      setError("Download URL is missing.");
      return;
    }

    try {
      const blob = await downloadCsv(result.download_url);
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = result?.output_filename || "fraud_predictions.csv";
      document.body.appendChild(link);
      link.click();

      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "Download failed.");
    }
  }

  return (
    <div className="page">
      <section className="card upload-card">
        <div className="card-header-row">
          <div>
            <h3>Upload CSV File</h3>
            <p>
              Upload transaction data and generate fraud risk predictions.
            </p>
          </div>

          <div className="upload-icon">
            <FileUp size={28} />
          </div>
        </div>

        <form className="upload-form" onSubmit={handleUpload}>
          <label className="file-drop-zone">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
            />

            <div>
              <strong>
                {selectedFile ? selectedFile.name : "Choose a CSV file"}
              </strong>

              <span>
                Required columns: transaction_id, user_id, device_id, card_id,
                ip_address, merchant_id, amount, timestamp, channel, country
              </span>
            </div>
          </label>

          <label className="llm-toggle-row">
            <input
              type="checkbox"
              checked={useLlmForAllRows}
              onChange={(event) => setUseLlmForAllRows(event.target.checked)}
            />

            <span>
              <Sparkles size={17} />
              Use LLM explanations for all valid rows
            </span>
          </label>

          <p className="helper-text">
            When enabled, approved transactions also get LLM explanations.
            This is slower but gives better explanations for every valid row.
          </p>

          {error && <div className="error-box">{error}</div>}

          <button className="primary-button" disabled={uploading}>
            {uploading ? (
              <>
                <Loader2 size={18} className="spin" />
                Uploading and predicting...
              </>
            ) : (
              <>
                <FileUp size={18} />
                Upload and Predict
              </>
            )}
          </button>
        </form>
      </section>

      {result && (
        <section className="card results-card">
          <div className="card-header-row">
            <div>
              <h3>Prediction Results</h3>
              <p>Batch ID: {result.batch_id}</p>
            </div>

            <div className="results-actions">
              {result.download_url && (
                <button className="secondary-button" onClick={handleDownload}>
                  <Download size={17} />
                  Download CSV
                </button>
              )}

              {goToPage && (
                <button
                  className="secondary-button"
                  onClick={() => goToPage("history")}
                >
                  View Previous Uploads
                </button>
              )}
            </div>
          </div>

          {result.summary && (
            <div className="summary-grid">
              <div className="summary-item">
                <span>Total Rows</span>
                <strong>{result.summary.total_rows ?? "-"}</strong>
              </div>

              <div className="summary-item">
                <span>Approved</span>
                <strong>{result.summary.approved ?? "-"}</strong>
              </div>

              <div className="summary-item">
                <span>Review</span>
                <strong>{result.summary.review ?? "-"}</strong>
              </div>

              <div className="summary-item">
                <span>Declined</span>
                <strong>{result.summary.declined ?? "-"}</strong>
              </div>
            </div>
          )}

          <ResultsTable rows={result.predictions || result.results || []} />
        </section>
      )}
    </div>
  );
}