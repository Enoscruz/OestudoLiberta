import type { Metadata } from "next";
import { Suspense } from "react";

import { CatalogGridSkeleton, CatalogUnavailable } from "@/components/catalog/catalog-states";
import { CourseGrid } from "@/components/catalog/course-card";
import { fetchCategories, fetchCourses } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "Cursos",
  description: "Catálogo de cursos disponíveis na OestudoLiberta.",
};

function firstParam(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default function CoursesPage({ searchParams }: PageProps<"/cursos">) {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-12">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-bold font-display tracking-wide text-bone">Catálogo de cursos</h1>
        <p className="mt-2 text-slate-600">
          Escolha um curso, assista às aulas curtas e estude no seu ritmo. Cada curso é comprado
          separadamente.
        </p>
      </header>

      <Suspense fallback={<ResultsSkeleton />}>
        <CourseResults searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

function ResultsSkeleton() {
  return (
    <div className="mt-8">
      <CatalogGridSkeleton count={6} />
    </div>
  );
}

async function CourseResults({
  searchParams,
}: Pick<PageProps<"/cursos">, "searchParams">) {
  const params = await searchParams;
  const rawCategory = firstParam(params.categoria);
  const parsedCategory = rawCategory ? Number.parseInt(rawCategory, 10) : Number.NaN;
  const categoryId = Number.isInteger(parsedCategory) ? parsedCategory : undefined;
  const search = firstParam(params.q)?.trim() || undefined;

  let data;
  try {
    data = await Promise.all([
      fetchCategories(),
      fetchCourses({ categoryId, search }),
    ]);
  } catch {
    return (
      <div className="mt-8">
        <CatalogUnavailable />
      </div>
    );
  }

  const [categories, courses] = data;

  return (
    <>
      <form
        method="get"
        action="/cursos"
        className="mt-8 flex flex-col gap-3 rounded-none border border-line bg-surface p-4 sm:flex-row sm:items-end"
      >
        <div className="flex flex-1 flex-col gap-1.5">
          <label htmlFor="q" className="text-sm font-medium text-slate-700">
            Buscar
          </label>
          <input
            id="q"
            name="q"
            type="search"
            defaultValue={search ?? ""}
            placeholder="Título do curso"
            className="rounded-none border border-slate-300 bg-surface px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 focus:outline-none"
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:w-56">
          <label htmlFor="categoria" className="text-sm font-medium text-slate-700">
            Categoria
          </label>
          <select
            id="categoria"
            name="categoria"
            defaultValue={categoryId ? String(categoryId) : ""}
            className="rounded-none border border-slate-300 bg-surface px-3 py-2.5 text-sm text-slate-900 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 focus:outline-none"
          >
            <option value="">Todas as categorias</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          className="rounded-none bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white font-mono uppercase tracking-[0.18em] hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
        >
          Filtrar
        </button>
      </form>

      <p className="mt-6 text-sm text-slate-500">
        {courses.length === 1 ? "1 curso encontrado" : `${courses.length} cursos encontrados`}
      </p>

      {courses.length > 0 ? (
        <div className="mt-4">
          <CourseGrid courses={courses} />
        </div>
      ) : (
        <p className="mt-4 rounded-none border border-dashed border-line bg-surface p-6 text-sm text-slate-600">
          Nenhum curso encontrado com esses filtros. Tente outra busca ou categoria.
        </p>
      )}
    </>
  );
}
