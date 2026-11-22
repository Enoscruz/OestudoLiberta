/**
 * Consultas do catálogo público (executadas no servidor).
 *
 * `connection()` mantém estas consultas fora do prerender: o shell estático das
 * páginas é gerado sem depender de o backend estar no ar durante o build.
 */

import { connection } from "next/server";

import { apiBaseUrl } from "@/lib/env";
import type { CatalogCategory, CatalogCourse, CatalogCourseDetail } from "@/types/api";

export const CATALOG_UNAVAILABLE_MESSAGE =
  "Não foi possível carregar o catálogo agora. Verifique se o backend está em execução.";

/** Falha ao consultar o catálogo no backend. */
export class CatalogUnavailableError extends Error {
  constructor() {
    super(CATALOG_UNAVAILABLE_MESSAGE);
    this.name = "CatalogUnavailableError";
  }
}

async function fetchJson(path: string): Promise<Response> {
  await connection();
  try {
    return await fetch(`${apiBaseUrl}${path}`, { cache: "no-store" });
  } catch {
    throw new CatalogUnavailableError();
  }
}

/** Lista as categorias ativas exibidas na vitrine. */
export async function fetchCategories(): Promise<CatalogCategory[]> {
  const response = await fetchJson("/catalog/categories");
  if (!response.ok) {
    throw new CatalogUnavailableError();
  }
  return (await response.json()) as CatalogCategory[];
}

/** Lista os cursos publicados, opcionalmente filtrados. */
export async function fetchCourses(
  filters: { categoryId?: number; search?: string } = {},
): Promise<CatalogCourse[]> {
  const params = new URLSearchParams();
  if (filters.categoryId !== undefined) {
    params.set("category_id", String(filters.categoryId));
  }
  if (filters.search) {
    params.set("search", filters.search);
  }
  const query = params.toString();

  const response = await fetchJson(`/catalog/courses${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new CatalogUnavailableError();
  }
  return (await response.json()) as CatalogCourse[];
}

/** Detalha um curso publicado; devolve `null` quando ele não existe. */
export async function fetchCourse(courseId: string): Promise<CatalogCourseDetail | null> {
  const response = await fetchJson(`/catalog/courses/${encodeURIComponent(courseId)}`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new CatalogUnavailableError();
  }
  return (await response.json()) as CatalogCourseDetail;
}
