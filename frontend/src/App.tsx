import { useState } from "react";
import { useAuth } from "./auth/useAuth";
import LocationMonitor from "./components/LocationMonitor";

function App() {
  const {
    isAuthenticated,
    user,
    authenticationLevel,
    logout,
    getAccessToken,
  } = useAuth();

  const [backendResult, setBackendResult] = useState("");
  const [loading, setLoading] = useState(false);

  const testBackendAuthentication = async () => {
    setLoading(true);
    setBackendResult("");

    try {
      const accessToken = await getAccessToken();

      const response = await fetch(
        "http://127.0.0.1:8000/auth/me",
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        },
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail || "Backend authentication failed.",
        );
      }

      setBackendResult(
        JSON.stringify(result, null, 2),
      );
    } catch (error) {
      setBackendResult(
        error instanceof Error
          ? error.message
          : "Unknown error occurred.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">

      {/* Background location monitoring */}
      <LocationMonitor />

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">ZT</div>

          <div>
            <h1>ZeroTrust</h1>
            <span>IDENTITY & ACCESS MANAGEMENT</span>
          </div>
        </div>

        <div className="topbar-right">
          <div className="connection-status">
            <span className="status-dot" />
            System Online
          </div>

          <button
            className="logout-button"
            onClick={logout}
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="dashboard">

        <section className="welcome-section">
          <div>
            <span className="eyebrow">
              SECURITY OVERVIEW
            </span>

            <h2>Security Dashboard</h2>

            <p>
              Monitor your identity, device and security
              status in one place.
            </p>
          </div>

          <div className="session-badge">
            <span className="status-dot" />
            Active Session
          </div>
        </section>

        <section className="overview-grid">

          <div className="info-card identity-card">
            <div className="card-heading">
              <div className="card-icon purple-icon">
                ◈
              </div>

              <span className="card-label">
                IDENTITY
              </span>

              <span className="verified-badge">
                Verified
              </span>
            </div>

            <h3>
              {user?.name || user?.username || "User"}
            </h3>

            <p className="muted-text">
              {user?.email || "Email unavailable"}
            </p>

            <div className="card-divider" />

            <div className="detail-row">
              <span>Authentication</span>

              <strong>
                {isAuthenticated
                  ? "Authenticated"
                  : "Not authenticated"}
              </strong>
            </div>

            <div className="detail-row">
              <span>MFA Level</span>

              <strong>
                {authenticationLevel === "2"
                  ? "Level 2 · MFA"
                  : authenticationLevel || "Unavailable"}
              </strong>
            </div>
          </div>

          <div className="info-card backend-card">
            <div className="card-heading">
              <div className="card-icon blue-icon">
                ⌘
              </div>

              <span className="card-label">
                BACKEND
              </span>
            </div>

            <h3>API Authentication</h3>

            <p className="muted-text">
              Verify your authenticated session with the
              FastAPI backend.
            </p>

            <button
              className="secondary-button"
              onClick={testBackendAuthentication}
              disabled={loading || !isAuthenticated}
            >
              {loading
                ? "Verifying..."
                : "Verify Connection →"}
            </button>

            {backendResult && (
              <pre className="result-code">
                {backendResult}
              </pre>
            )}
          </div>

        </section>

        <footer className="dashboard-footer">
          <span>Adaptive Zero Trust IAM</span>

          <span>
            Identity · Context · Continuous Verification
          </span>
        </footer>

      </main>
    </div>
  );
}

export default App;