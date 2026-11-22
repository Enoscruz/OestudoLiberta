"use client";

import type { ReactNode } from "react";

import { AuthProvider } from "@/contexts/auth-context";

/**
 * Agrupa os provedores de contexto do cliente.
 *
 * Fica o mais próximo possível de `{children}` para manter o restante do
 * layout renderizável no servidor.
 */
export function Providers({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
