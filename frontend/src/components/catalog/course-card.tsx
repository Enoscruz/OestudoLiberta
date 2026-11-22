import Link from "next/link";

import { formatPrice } from "@/lib/format";
import type { CatalogCourse } from "@/types/api";

function lessonCountLabel(count: number): string {
  if (count === 0) {
    return "Conteúdo em breve";
  }
  return count === 1 ? "1 aula" : `${count} aulas`;
}

function CourseCover({ course }: { course: CatalogCourse }) {
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
    <div className="relative flex h-40 w-full items-center justify-center bg-linear-to-br from-brand-700 via-brand-600 to-void">
      <span className="font-display text-4xl font-bold text-bone/80">
        {course.title.charAt(0).toUpperCase()}
      </span>
    </div>
  );
}

export function CourseCard({ course }: { course: CatalogCourse }) {
  return (
    <Link
      href={`/cursos/${course.id}`}
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

        <div className="mt-auto flex items-center justify-between gap-4 border-t border-line pt-4">
          <span className="font-mono text-xs tracking-wider text-slate-500 uppercase">
            {lessonCountLabel(course.lessons_count)}
          </span>
          <span className="font-mono text-base text-bone">{formatPrice(course.price)}</span>
        </div>
      </div>
    </Link>
  );
}

export function CourseGrid({ courses }: { courses: CatalogCourse[] }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {courses.map((course) => (
        <CourseCard key={course.id} course={course} />
      ))}
    </div>
  );
}
