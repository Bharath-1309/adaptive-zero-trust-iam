import { useState } from "react";
import { useAuth } from "./auth/useAuth";

function App() {
  const {
    isAuthenticated,
    user,
    authenticationLevel,
    logout,
    getAccessToken,
  } = useAuth();

  const [backendResult, setBackendResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const testBackendAuthentication = async () => {
    setLoading(true);
    setBackendResult("");

    try {
      const accessToken = await getAccessToken();

      const response = await fetch("http://127.0.0.1:8000/auth/me", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Backend authentication failed.");
      }

      setBackendResult(JSON.stringify(result, null, 2));
    } catch (error) {
      setBackendResult(
        error instanceof Error ? error.message : "Unknown error occurred.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: "30px", fontFamily: "Arial, sans-serif" }}>
      <h1>Adaptive Zero Trust IAM</h1>

      <h2>Authentication Status</h2>

      <p>
        <strong>Authenticated:</strong>{" "}
        {isAuthenticated ? "Yes" : "No"}
      </p>

      <p>
        <strong>Authentication Level:</strong>{" "}
        {authenticationLevel ?? "Unavailable"}
      </p>

      <h2>User Information</h2>

      <p>
        <strong>Username:</strong> {user?.username ?? "Unavailable"}
      </p>

      <p>
        <strong>Email:</strong> {user?.email ?? "Unavailable"}
      </p>

      <p>
        <strong>Name:</strong> {user?.name ?? "Unavailable"}
      </p>

      <h2>Backend Authentication Test</h2>

      <button
        type="button"
        onClick={testBackendAuthentication}
        disabled={loading || !isAuthenticated}
      >
        {loading ? "Testing..." : "Test Backend Authentication"}
      </button>

      {backendResult && (
        <pre
          style={{
            marginTop: "20px",
            padding: "15px",
            backgroundColor: "#f0f0f0",
            whiteSpace: "pre-wrap",
          }}
        >
          {backendResult}
        </pre>
      )}

      <br />
      <br />

      <button type="button" onClick={logout}>
        Logout
      </button>
    </main>
  );
}

export default App;
