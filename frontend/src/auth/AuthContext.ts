import { createContext } from "react";

export interface AuthUser {
  id?: string;
  username?: string;
  email?: string;
  name?: string;
  firstName?: string;
  lastName?: string;
}

export interface AuthContextType {
  isAuthenticated: boolean;
  user: AuthUser | null;
  authenticationLevel: string | undefined;
  login: () => void;
  logout: () => void;
  getAccessToken: () => Promise<string>;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);