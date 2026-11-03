import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import keycloak from "./auth/keycloak";

async function initializeApp() {
try {
const authenticated = await keycloak.init({
pkceMethod: "S256",
checkLoginIframe: false,
});


if (!authenticated) {
  await keycloak.login({
    acrValues: "2",
  });
  return;
}

const authenticationLevel = keycloak.tokenParsed?.acr;

console.log("Keycloak authenticated:", keycloak.authenticated);
console.log("Authentication level (acr):", authenticationLevel);

if (authenticationLevel !== "2") {
  await keycloak.login({
    acrValues: "2",
  });
  return;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);


} catch (error) {
console.error("Keycloak initialization failed:", error);


document.getElementById("root")!.innerHTML =
  "<h2>Authentication initialization failed. Please try again.</h2>";


}
}

initializeApp();
