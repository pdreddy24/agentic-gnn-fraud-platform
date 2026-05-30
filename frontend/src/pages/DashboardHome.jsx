import { useEffect, useState } from "react";
import { ArrowRight, Database, FileUp, ShieldAlert, TrendingUp } from "lucide-react";
import { getJson } from "../api/client.js";
import MetricCard from "../components/MetricCard.jsx";
import BatchTable from "../components/BatchTable.jsx";

export default function DashboardHome({ goToPage, lastUploadResult }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  async function loadHistory() {
    try {
      const result = await getJson("/uploads/history?limit=5", true);
      setHistory(result.batches || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadHistory();
  }, [lastUploadResult]);

  const latest = history[0];

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Overview of recent fraud prediction uploads.</p>
        </div>
        <button className="primary-button" onClick={() => goToPage("upload")}>
          Upload CSV <ArrowRight size={18} />
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="metrics-grid">
        <MetricCard icon={Database} label="Total Uploads" value={history.length} hint="Recent uploads loaded" />
        <MetricCard icon={TrendingUp} label="Latest Avg Risk" value={latest ? latest.average_risk : "0.0000"} hint={latest ? latest.filename : "No upload yet"} />
        <MetricCard icon={ShieldAlert} label="Latest Review" value={latest ? latest.review_count : 0} hint="Manual review cases" />
        <MetricCard icon={FileUp} label="Latest Rows" value={latest ? latest.successful_rows : 0} hint="Successful predictions" />
      </div>

      <div className="card">
        <div className="section-title">
          <div>
            <h3>Recent Uploads</h3>
            <p>Your most recent stored batches.</p>
          </div>
          <button className="secondary-button" onClick={() => goToPage("history")}>
            View All
          </button>
        </div>

        <BatchTable batches={history} compact />
      </div>
    </section>
  );
}
