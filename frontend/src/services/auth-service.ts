/**
 * Chamadas de autenticação ao backend.
 *
 * O backend valida o ID Token do Firebase e sincroniza o usuário no PostgreSQL.
 * O frontend nunca decide o papel do usuário: apenas exibe o que a API devolve.
 */

import { apiFetch } from "@/lib/api";
import type { User } from "@/types/api";

export function fetchMe(token: string): Promise<User> {
  return apiFetch<User>("/auth/me", { token });
}
