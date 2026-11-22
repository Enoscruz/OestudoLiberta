import Link from "next/link";

import type { MyCourse } from "@/types/api";

function lessonsLabel(count: number): string {
  if (count === 0) {
    return "Conteúdo em breve";
  }
  return count === 1 ? "1 aula liberada" : `${count} aulas liberadas`;
}

function CourseCover({ course }: { course: MyCourse }) {
  if (course.cover_image) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={course.cover_image}
        alt=""
        loading="lazy"
        className="h-40 w-full object-cover opacity-90 transition group-hover:opacity-100"
      />
    );
  }

  return (
    <div className="flex h-40 w-full items-center justify-center bg-linear-to-br from-brand-700 via-brand-600 to-void">
      <span className="font-display text-4xl font-bold text-bone/80">
        {course.title.charAt(0).toUpperCase()}
      </span>
    </div>
  );
}

export function MyCourseCard({ course }: { course: MyCourse }) {
  const finished =
    course.lessons_count > 0 && course.completed_lessons >= course.lessons_count;
  const started = course.completed_lessons > 0;

  return (
    <Link
      href={`/dashboard/cursos/${course.id}`}
      className="group flex flex-col overflow-hidden border border-line bg-surface transition hover:border-blood hover:shadow-[0_0_40px_-16px_var(--color-blood-bright)]"
    >
      <CourseCover course={course} />

      <div className="flex flex-1 flex-col gap-2 p-5">
        {course.category_name ? (
          <span className="font-mono text-[0.68rem] tracking-[0.2em] text-blood uppercase">
            {course.category_name}
          </span>
        ) : null}

        <h3 className="font-display text-lg leading-snug tracking-wide text-bone transition group-hover:text-blood-bright">
          {course.title}
        </h3>

        {course.description ? (
          <p className="line-clamp-3 text-sm text-slate-500">{course.description}</p>
        ) : null}

        <div className="mt-auto flex flex-col gap-3 pt-3">
          {course.lessons_count > 0 ? (
            <div>
              <div className="flex items-center justify-between gap-4 font-mono text-[0.68rem] tracking-wider text-slate-500 uppercase">
                <span>{lessonsLabel(course.lessons_count)}</span>
                <span className={finished ? "text-bone" : "text-blood-bright"}>
                  {finished ? "Concluído" : `${course.progress_percent}%`}
                </span>
              </div>
              <div className="mt-2 h-1 w-full overflow-hidden bg-slate-100">
                <div
                  className={`h-full ${
                    finished ? "bg-bone" : "bg-brand-600"
                  }`}
                  style={{ width: `${course.progress_percent}%` }}
                />
              </div>
            </div>
          ) : (
            <span className="font-mono text-xs tracking-wider text-slate-500 uppercase">
              {lessonsLabel(course.lessons_count)}
            </span>
          )}

          <span className="font-mono text-[0.7rem] tracking-[0.18em] text-blood uppercase transition group-hover:text-blood-bright">
            {started ? "Continuar →" : "Assistir →"}
          </span>
        </div>
      </div>
    </Link>
  );
}

export function MyCourseGrid({ courses }: { courses: MyCourse[] }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {courses.map((course) => (
        <MyCourseCard key={course.id} course={course} />
      ))}
    </div>
  );
}

export function MyCoursesEmpty() {
  return (
    <div className="border border-dashed border-slate-300 bg-surface p-8 text-center">
      <h2 className="font-display text-lg tracking-wide text-bone">Você ainda não tem cursos</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
        Os cursos aparecem aqui assim que o pagamento é confirmado. Enquanto isso, explore o
        catálogo e escolha o que estudar.
      </p>
      <Link
        href="/cursos"
        className="mt-6 inline-block bg-brand-600 px-5 py-3 font-mono text-[0.72rem] font-semibold tracking-[0.18em] text-white uppercase transition hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
      >
        Ver catálogo de cursos
      </Link>
    </div>
  );
}
