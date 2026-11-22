"use client";

/**
 * Contexto de autenticação.
 *
 * Combina o Firebase Authentication (cadastro, login, logout, recuperação de
 * senha e confirmação de e-mail) com a sincronização do usuário no backend
 * (`GET /auth/me`), que é a fonte de verdade sobre papéis (ADMIN/STUDENT).
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  reload,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
  type User as FirebaseUser,
} from "firebase/auth";

import { ApiError } from "@/lib/api";
import { isFirebaseConfigured } from "@/lib/env";
import { translateAuthError } from "@/lib/firebase-errors";
import { getFirebaseAuth } from "@/lib/firebase";
import { fetchMe } from "@/services/auth-service";
import type { User } from "@/types/api";

interface AuthContextValue {
  /** Usuário conforme persistido no backend. */
  user: User | null;
  /** `true` enquanto a sessão inicial está sendo restaurada. */
  loading: boolean;
  /** Credenciais Web do Firebase ainda não configuradas. */
  firebaseReady: boolean;
  /** Falha ao sincronizar com o backend (ex.: Firebase não configurado no servidor). */
  syncError: string | null;
  register: (name: string, email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  resendVerificationEmail: () => Promise<void>;
  /** Recarrega o usuário do Firebase e refaz a sincronização com o backend. */
  refresh: () => Promise<void>;
  /** ID Token do Firebase do usuário atual (ou `null` se não houver sessão). */
  getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function syncWithBackend(firebaseUser: FirebaseUser | null): Promise<{
  user: User | null;
  syncError: string | null;
}> {
  if (!firebaseUser) {
    return { user: null, syncError: null };
  }
  try {
    const token = await firebaseUser.getIdToken();
    return { user: await fetchMe(token), syncError: null };
  } catch (error) {
    const detail =
      error instanceof ApiError
        ? error.message
        : "Não foi possível sincronizar sua conta com o servidor.";
    return { user: null, syncError: detail };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  // Sem Firebase configurado não há sessão a restaurar, então já começa carregado.
  const [loading, setLoading] = useState(isFirebaseConfigured);
  const [syncError, setSyncError] = useState<string | null>(null);

  useEffect(() => {
    const auth = getFirebaseAuth();
    if (!auth) {
      return;
    }

    return onAuthStateChanged(auth, async (firebaseUser) => {
      const result = await syncWithBackend(firebaseUser);
      setUser(result.user);
      setSyncError(result.syncError);
      setLoading(false);
    });
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const auth = getFirebaseAuth();
      if (!auth) {
        throw new Error("Firebase não configurado. Preencha o arquivo .env.local.");
      }
      try {
        const credential = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(credential.user, { displayName: name });
        // Confirmação de e-mail é obrigatória para acessar as áreas restritas.
        await sendEmailVerification(credential.user);
      } catch (error) {
        throw new Error(translateAuthError(error));
      }
    },
    [],
  );

  const login = useCallback(async (email: string, password: string) => {
    const auth = getFirebaseAuth();
    if (!auth) {
      throw new Error("Firebase não configurado. Preencha o arquivo .env.local.");
    }
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (error) {
      throw new Error(translateAuthError(error));
    }
  }, []);

  const logout = useCallback(async () => {
    const auth = getFirebaseAuth();
    if (auth) {
      await signOut(auth);
    }
    setUser(null);
    setSyncError(null);
  }, []);

  const resetPassword = useCallback(async (email: string) => {
    const auth = getFirebaseAuth();
    if (!auth) {
      throw new Error("Firebase não configurado. Preencha o arquivo .env.local.");
    }
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (error) {
      throw new Error(translateAuthError(error));
    }
  }, []);

  const resendVerificationEmail = useCallback(async () => {
    const auth = getFirebaseAuth();
    if (!auth?.currentUser) {
      throw new Error("Nenhum usuário autenticado.");
    }
    try {
      await sendEmailVerification(auth.currentUser);
    } catch (error) {
      throw new Error(translateAuthError(error));
    }
  }, []);

  const refresh = useCallback(async () => {
    const auth = getFirebaseAuth();
    const firebaseUser = auth?.currentUser ?? null;
    if (firebaseUser) {
      await reload(firebaseUser);
    }
    const result = await syncWithBackend(firebaseUser);
    setUser(result.user);
    setSyncError(result.syncError);
  }, []);

  const getIdToken = useCallback(async () => {
    const auth = getFirebaseAuth();
    const firebaseUser = auth?.currentUser ?? null;
    if (!firebaseUser) {
      return null;
    }
    return firebaseUser.getIdToken();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      firebaseReady: isFirebaseConfigured,
      syncError,
      register,
      login,
      logout,
      resetPassword,
      resendVerificationEmail,
      refresh,
      getIdToken,
    }),
    [
      user,
      loading,
      syncError,
      register,
      login,
      logout,
      resetPassword,
      resendVerificationEmail,
      refresh,
      getIdToken,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de <AuthProvider>.");
  }
  return context;
}
