"use client";

/**
 * Protege uma rota no cliente: aguarda a sessão e redireciona para o login
 * quando não há usuário autenticado.
 *
 * É uma conveniência de interface — a autorização real é sempre do backend.
 */

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/contexts/auth-context";

export function useRequireAuth(options: { adminOnly?: boolean } = {}): {
  ready: boolean;
} {
  const { user, loading } = useAuth();
  const router = useRouter();
  const { adminOnly = false } = options;

  useEffect(() => {
    if (loading) {
      return;
    }
    if (!user) {
      router.replace("/login");
      return;
    }
    if (adminOnly && user.role.name !== "ADMIN") {
      router.replace("/dashboard");
    }
  }, [loading, user, adminOnly, router]);

  const allowed = Boolean(user) && (!adminOnly || user?.role.name === "ADMIN");
  return { ready: !loading && allowed };
}
