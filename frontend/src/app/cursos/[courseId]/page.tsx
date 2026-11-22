import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CatalogUnavailable } from "@/components/catalog/catalog-states";
import { BuyCourseButton } from "@/components/checkout/buy-course-button";
import { fetchCourse } from "@/lib/catalog";
import { formatDuration, formatPrice } from "@/lib/format";

// A página depende inteiramente do `courseId`; bloquear a navegação mantém o
// status HTTP correto (404) em vez de um shell estático com soft-404.
export const instant = false;

export const metadata: Metadata = {
  title: "Curso",
};

export default async function CourseDetailPage({ params }: PageProps<"/cursos/[courseId]">) {
  const { courseId } = await params;

  // Um id não numérico nunca corresponde a um curso: evita exibir o aviso de
  // "catálogo indisponível" (e um 422 do backend) para uma URL inválida.
  if (!/^\d+$/.test(courseId)) {
    notFound();
  }

  let course;
  try {
    course = await fetchCourse(courseId);
  } catch {
    return (
      <main className="mx-auto w-full max-w-4xl px-4 py-12">
        <CatalogUnavailable />
      </main>
    );
  }

  if (!course) {
    notFound();
  }

  const totalSeconds = course.lessons.reduce(
    (total, lesson) => total + (lesson.duration_seconds ?? 0),
    0,
  );
  const totalDuration = formatDuration(totalSeconds);

  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-12">
      <Link href="/cursos" className="text-sm font-medium text-brand-600 hover:text-blood-bright">
        ← Voltar ao catálogo
      </Link>

      <article className="mt-8">
        {course.cover_image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={course.cover_image}
            alt=""
            className="h-56 w-full rounded-none object-cover sm:h-72"
          />
        ) : null}

        <div className="mt-6">
          {course.category_name ? (
            <span className="eyebrow text-blood">
              {course.category_name}
            </span>
          ) : null}
          <h1 className="mt-2 text-3xl font-bold font-display tracking-wide text-bone">{course.title}</h1>
          {course.description ? <p className="mt-4 text-slate-600">{course.description}</p> : null}
        </div>

        <section className="mt-8 flex flex-col gap-4 rounded-none border border-line bg-surface p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-2xl font-bold text-slate-900">{formatPrice(course.price)}</p>
            <p className="mt-1 text-sm text-slate-500">Acesso permanente ao curso adquirido.</p>
          </div>
          <BuyCourseButton courseId={course.id} free={Number(course.price) === 0} />
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold font-display tracking-wide text-bone">
            Conteúdo do curso
            {totalDuration ? (
              <span className="ml-2 text-sm font-normal text-slate-500">({totalDuration})</span>
            ) : null}
          </h2>

          {course.lessons.length > 0 ? (
            <ol className="mt-4 divide-y divide-slate-200 overflow-hidden rounded-none border border-line bg-surface">
              {course.lessons.map((lesson) => {
                const duration = formatDuration(lesson.duration_seconds);
                return (
                  <li key={lesson.id} className="flex items-start gap-4 p-4">
                    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-none bg-brand-50 text-xs font-semibold text-brand-700">
                      {lesson.lesson_order}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-slate-900">{lesson.title}</p>
                      {lesson.description ? (
                        <p className="mt-1 text-sm text-slate-600">{lesson.description}</p>
                      ) : null}
                    </div>
                    {duration ? (
                      <span className="shrink-0 text-sm text-slate-500">{duration}</span>
                    ) : null}
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="mt-4 rounded-none border border-dashed border-line bg-surface p-6 text-sm text-slate-600">
              As aulas deste curso ainda estão sendo publicadas.
            </p>
          )}
        </section>
      </article>
    </main>
  );
}
