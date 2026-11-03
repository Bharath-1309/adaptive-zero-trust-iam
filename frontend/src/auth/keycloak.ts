import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "http://localhost:8080",
  realm: "adaptive-iam",
  clientId: "adaptive-iam-frontend",
});

export default keycloak;