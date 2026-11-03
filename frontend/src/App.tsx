import { useAuth } from "./auth/useAuth";

function App() {
  const {
    isAuthenticated,
    user,
    authenticationLevel,
    logout,
  } = useAuth();

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

      <button type="button" onClick={logout}>
        Logout
      </button>
    </main>
  );
}

export default App;