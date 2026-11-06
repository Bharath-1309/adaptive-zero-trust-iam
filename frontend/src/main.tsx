import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import keycloak from "./auth/keycloak";
import { AuthProvider } from "./auth/AuthProvider";

async function initializeApp() {
  try {
    const authenticated = await keycloak.init({
      pkceMethod: "S256",
      checkLoginIframe: false,
    });

    // Normal sign-in only. Stronger authentication (MFA) is requested
    // later, and only when the backend returns a STEP_UP decision.
    if (!authenticated) {
      await keycloak.login();
      return;
    }

    console.log("Keycloak authenticated:", keycloak.authenticated);
    console.log("Authentication level (acr):", keycloak.tokenParsed?.acr);

    createRoot(document.getElementById("root")!).render(
      <AuthProvider>
        <App />
      </AuthProvider>,
    );
  } catch (error) {
    console.error("Keycloak initialization failed:", error);

    document.getElementById("root")!.innerHTML =
      "<h2>Authentication initialization failed. Please try again.</h2>";
  }
}

initializeApp();