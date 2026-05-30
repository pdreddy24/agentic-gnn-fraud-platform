import { useState } from "react";
import {
  BarChart3,
  Clock,
  FileUp,
  History,
  LogOut,
  ShieldCheck,
  SplitSquareVertical,
} from "lucide-react";

import {
  clearToken,
  getSavedUser,
  getToken,
} from "./api/client.js";

import Login from "./pages/Login.jsx";
import Upload from "./pages/Upload.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import Compare from "./pages/Compare.jsx";
import DashboardHome from "./pages/DashboardHome.jsx";

const navItems = [
  { id: "upload", label: "Upload Data", icon: FileUp },
  { id: "dashboard", label: "Dashboard", icon: BarChart3 },
  { id: "history", label: "Previous Uploads", icon: History },
  { id: "compare", label: "Compare Uploads", icon: SplitSquareVertical },
];

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(Boolean(getToken()));
  const [user, setUser] = useState(getSavedUser());
  const [activePage, setActivePage] = useState("upload");
  const [lastUploadResult, setLastUploadResult] = useState(null);

  function handleLogin(loggedInUser) {
    setUser(loggedInUser);
    setIsLoggedIn(true);
    setActivePage("upload");
  }

  function handleLogout() {
    clearToken();
    setUser(null);
    setIsLoggedIn(false);
    setActivePage("upload");
    setLastUploadResult(null);
  }

  if (!isLoggedIn) {
    return <Login onLoginSuccess={handleLogin} />;
  }

  const Page = {
    upload: Upload,
    dashboard: DashboardHome,
    history: HistoryPage,
    compare: Compare,
  }[activePage];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={26} />
          </div>

          <div>
            <h1>Fraud AI</h1>
            <p>Version 2</p>
          </div>
        </div>

        <nav className="nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activePage === item.id;

            return (
              <button
                key={item.id}
                className={`nav-item ${active ? "active" : ""}`}
                onClick={() => setActivePage(item.id)}
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="avatar">
              {user?.email?.[0]?.toUpperCase() || "U"}
            </div>

            <div>
              <p className="user-label">Signed in</p>
              <p className="user-email">
                {user?.email || "user@fraud-ai.local"}
              </p>
            </div>
          </div>

          <button className="logout-button-v1" onClick={handleLogout}>
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h2>
              {activePage === "upload"
                ? "Upload Transaction Data"
                : "Hybrid Fraud Detection Platform"}
            </h2>

            <p>
              {activePage === "upload"
                ? "Upload a CSV file and predict fraud risk for every transaction."
                : "Predict risk, store previous results, and compare transaction batches."}
            </p>
          </div>

          <div className="status-pill">
            <Clock size={16} />
            Version 2
          </div>
        </header>

        <Page
          lastUploadResult={lastUploadResult}
          setLastUploadResult={setLastUploadResult}
          goToPage={setActivePage}
        />
      </main>
    </div>
  );
}