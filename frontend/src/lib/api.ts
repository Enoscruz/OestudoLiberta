/**
 * Cliente HTTP para a API do backend.
 *
 * Centraliza a URL base, o cabeçalho `Authorization` (ID Token do Firebase) e a
 * tradução de respostas de erro em `ApiError`.
 */

import { apiBaseUrl } from "./env";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  token?: string | null;
  body?: unknown;
  signal?: AbortSignal;
}

async function extractDetail(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // Resposta sem corpo JSON — usa a mensagem padrão abaixo.
  }
  return `A requisição falhou (status ${response.status}).`;
}

export async function apiFetch<T>(
  path: string,
  { method = "GET", token, body, signal }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await extractDetail(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** Mensagem legível de um erro da API, com um texto padrão para falhas inesperadas. */
export function describeApiError(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}
