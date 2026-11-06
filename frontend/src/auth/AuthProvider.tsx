import { useEffect, useState, type ReactNode } from "react";

import keycloak from "./keycloak";
import { AuthContext, type AuthUser } from "./AuthContext";

interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  authenticationLevel: string | undefined;
}

interface AuthProviderProps {
  children: ReactNode;
}

function getAuthState(): AuthState {
  if (!keycloak.authenticated || !keycloak.tokenParsed) {
    return {
      isAuthenticated: false,
      user: null,
      authenticationLevel: undefined,
    };
  }

  const token = keycloak.tokenParsed;

  return {
    isAuthenticated: true,
    user: {
      id: token.sub,
      username: token.preferred_username,
      email: token.email,
      name: token.name,
      firstName: token.given_name,
      lastName: token.family_name,
    },
    authenticationLevel:
      typeof token.acr === "string" ? token.acr : undefined,
  };
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>(getAuthState);

  useEffect(() => {
    const updateAuthState = () => {
      setAuthState(getAuthState());
    };

    keycloak.onAuthSuccess = updateAuthState;
    keycloak.onAuthRefreshSuccess = updateAuthState;
    keycloak.onAuthLogout = updateAuthState;

    keycloak.onTokenExpired = () => {
      void keycloak
        .updateToken(30)
        .then(updateAuthState)
        .catch((error) => {
          console.error("Token refresh failed:", error);
          updateAuthState();
        });
    };

    return () => {
      keycloak.onAuthSuccess = undefined;
      keycloak.onAuthRefreshSuccess = undefined;
      keycloak.onAuthLogout = undefined;
      keycloak.onTokenExpired = undefined;
    };
  }, []);

   const login = () => {
    void keycloak.login();
  };

  // Called only when the backend returns STEP_UP. The backend tells us
  // which authentication level it needs (required_acr); Keycloak then
  // runs the matching flow (level 2 = password + OTP).
  const stepUp = (requiredAcr: string) => {
    void keycloak.login({
      acrValues: requiredAcr,
      redirectUri: window.location.href,
    });
  };

  const logout = () => {
    void keycloak.logout({
      redirectUri: window.location.origin,
    });
  };

  const getAccessToken = async (): Promise<string> => {
    if (!keycloak.authenticated) {
      throw new Error("User is not authenticated.");
    }

    await keycloak.updateToken(30);

    if (!keycloak.token) {
      throw new Error("Access token is unavailable.");
    }

    return keycloak.token;
  };

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        stepUp,
        logout,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}