import Link from "next/link";
import { Suspense } from "react";

import { CatalogGridSkeleton, CatalogUnavailable } from "@/components/catalog/catalog-states";
import { CourseGrid } from "@/components/catalog/course-card";
import { WordsStagger } from "@/components/ui/words-stagger";
import { fetchCategories, fetchCourses } from "@/lib/catalog";

const HIGHLIGHTS = [
  {
    title: "Aulas curtas",
    description: "Vídeos de até 15 minutos, pensados para caber no seu dia e fixar o conteúdo.",
  },
  {
    title: "Pagamento por curso",
    description: "Você compra apenas o que quer estudar e mantém o acesso ao material adquirido.",
  },
  {
    title: "Progresso visível",
    description: "Continue exatamente de onde parou e acompanhe o que já concluiu.",
  },
];

const FEATURED_LIMIT = 6;

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-16 sm:py-24">
      <section className="max-w-3xl">
        <p className="eyebrow text-blood-bright">Estudar liberta</p>
        <h1 className="mt-5 font-display text-4xl leading-[1.08] tracking-tight text-bone sm:text-6xl">
          <WordsStagger delay={0.15} stagger={0.08} speed={0.7}>
            Cursos online objetivos, no seu ritmo.
          </WordsStagger>
        </h1>
        <p className="mt-7 max-w-2xl text-lg text-slate-500">
          Aprenda com aulas em vídeo curtas e bem organizadas por categoria. Compre apenas os
          cursos que fazem sentido para você e estude quando quiser.
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/cursos"
            className="bg-brand-600 px-6 py-3.5 text-center font-mono text-[0.72rem] font-semibold tracking-[0.18em] text-white uppercase transition hover:bg-brand-700 hover:shadow-[0_0_32px_-8px_var(--color-blood-bright)]"
          >
            Ver catálogo de cursos
          </Link>
          <Link
            href="/cadastro"
            className="border border-slate-300 px-6 py-3.5 text-center font-mono text-[0.72rem] font-semibold tracking-[0.18em] text-slate-600 uppercase transition hover:border-blood hover:text-blood-bright"
          >
            Criar minha conta
          </Link>
        </div>
      </section>

      {/* Fio de sangue separando a dobra principal. */}
      <div
        aria-hidden
        className="mt-16 h-px w-full bg-linear-to-r from-brand-600 via-blood-deep to-transparent"
      />

      <section className="mt-12 grid gap-px bg-line sm:grid-cols-3">
        {HIGHLIGHTS.map((item, index) => (
          <div key={item.title} className="bg-surface p-6">
            <span className="font-mono text-[0.7rem] tracking-[0.3em] text-blood">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h2 className="mt-3 font-display text-lg tracking-wide text-bone">{item.title}</h2>
            <p className="mt-2 text-sm text-slate-500">{item.description}</p>
          </div>
        ))}
      </section>

      <Suspense fallback={<FeaturedSkeleton />}>
        <CatalogOverview />
      </Suspense>
    </main>
  );
}

function FeaturedSkeleton() {
  return (
    <div className="mt-16">
      <h2 className="font-display text-xl tracking-wide text-bone">Cursos em destaque</h2>
      <div className="mt-6">
        <CatalogGridSkeleton />
      </div>
    </div>
  );
}

async function CatalogOverview() {
  let data;
  try {
    data = await Promise.all([fetchCategories(), fetchCourses()]);
  } catch {
    return (
      <div className="mt-16">
        <CatalogUnavailable />
      </div>
    );
  }

  const [categories, courses] = data;
  const featured = courses.slice(0, FEATURED_LIMIT);

  return (
    <>
      {categories.length > 0 ? (
        <section className="mt-16">
          <h2 className="font-display text-xl tracking-wide text-bone">Explore por categoria</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {categories.map((category) => (
              <Link
                key={category.id}
                href={`/cursos?categoria=${category.id}`}
                className="border border-line bg-surface px-4 py-2 font-mono text-[0.7rem] tracking-[0.16em] text-slate-500 uppercase transition hover:border-blood hover:text-blood-bright"
              >
                {category.name}
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mt-16">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="font-display text-xl tracking-wide text-bone">Cursos em destaque</h2>
          {courses.length > featured.length ? (
            <Link
              href="/cursos"
              className="font-mono text-[0.7rem] tracking-[0.18em] text-blood uppercase transition hover:text-blood-bright"
            >
              Ver todos
            </Link>
          ) : null}
        </div>

        {featured.length > 0 ? (
          <div className="mt-6">
            <CourseGrid courses={featured} />
          </div>
        ) : (
          <p className="mt-5 border border-dashed border-slate-300 bg-surface p-6 text-sm text-slate-500">
            Nenhum curso publicado ainda. Assim que os primeiros cursos forem liberados, eles
            aparecerão aqui.
          </p>
        )}
      </section>
    </>
  );
}
