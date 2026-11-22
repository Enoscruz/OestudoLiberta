"use client";

/**
 * Histórico de aprendizagem do aluno (`GET /me/history`).
 *
 * Os indicadores (cursos, concluídos, aulas e tempo assistido) e o percentual
 * de cada curso são calculados pelo backend a partir das aulas publicadas —
 * a interface apenas apresenta os números recebidos.
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { useAuth } from "@/contexts/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { ApiError } from "@/lib/api";
import { fetchLearningHistory } from "@/services/learning-service";
import type { LearningCourse, LearningHistory, LearningSummary } from "@/types/api";

interface LoadFailure {
  message: string;
  /** O backend recusou o acesso (e-mail não confirmado). */
  forbidden: boolean;
}

/** Tempo assistido em segundos no formato ``2 h 15 min`` (ou ``—`` sem registro). */
function formatWatched(seconds: number): string {
  if (seconds <= 0) {
    return "—";
  }
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  if (hours === 0) {
    return `${Math.max(1, minutes)} min`;
  }
  return minutes === 0 ? `${hours} h` : `${hours} h ${minutes} min`;
}

/** Data da última atividade no formato ``02/11/2026``. */
function formatDate(value: string | null): string {
  if (!value) {
    return "Sem registro";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Sem registro";
  }
  return date.toLocaleDateString("pt-BR");
}

export function HistoryContent() {
  const { ready } = useRequireAuth();
  const { getIdToken } = useAuth();
  const [history, setHistory] = useState<LearningHistory | null>(null);
  const [failure, setFailure] = useState<LoadFailure | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!ready) {
      return;
    }

    let active = true;
    getIdToken()
      .then((token) => {
        if (!token) {
          throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
        }
        return fetchLearningHistory(token);
      })
      .then((result) => {
        if (active) {
          setHistory(result);
          setFailure(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setHistory(null);
        setFailure(
          error instanceof ApiError
            ? { message: error.message, forbidden: error.status === 403 }
            : {
                message: "Não foi possível carregar seu histórico agora.",
                forbidden: false,
              },
        );
      });

    return () => {
      active = false;
    };
  }, [ready, getIdToken, reloadKey]);

  const reload = useCallback(() => {
    setFailure(null);
    setHistory(null);
    setReloadKey((key) => key + 1);
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-12">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-display tracking-wide text-bone">
            Histórico de aprendizagem
          </h1>
          <p className="mt-2 text-slate-600">
            Acompanhe o que você já estudou e retome de onde parou.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="text-sm font-semibold text-brand-600 hover:text-blood-bright"
        >
          ← Meus cursos
        </Link>
      </header>

      <section className="mt-8">
        {failure ? (
          <div className="flex flex-col gap-4">
            <Alert tone="warning" title="Não foi possível carregar seu histórico">
              {failure.message}
            </Alert>
            {failure.forbidden ? (
              <Link
                href="/verificar-email"
                className="self-start text-sm font-semibold text-brand-600 hover:text-blood-bright"
              >
                Confirmar e-mail para liberar o acesso →
              </Link>
            ) : (
              <button
                type="button"
                onClick={reload}
                className="self-start rounded-none bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white font-mono uppercase tracking-[0.18em] hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
              >
                Tentar novamente
              </button>
            )}
          </div>
        ) : history === null ? (
          <HistorySkeleton />
        ) : (
          <div className="flex flex-col gap-10">
            <SummaryCards summary={history.summary} />
            <CourseHistory courses={history.courses} />
          </div>
        )}
      </section>
    </main>
  );
}

function SummaryCards({ summary }: { summary: LearningSummary }) {
  const items = [
    { label: "Cursos liberados", value: String(summary.courses_owned) },
    { label: "Cursos concluídos", value: String(summary.courses_completed) },
    {
      label: "Aulas concluídas",
      value: `${summary.lessons_completed}/${summary.lessons_available}`,
    },
    { label: "Tempo assistido", value: formatWatched(summary.watched_seconds) },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-none border border-line bg-surface p-5"
        >
          <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            {item.label}
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{item.value}</p>
        </div>
      ))}
    </div>
  );
}

function CourseHistory({ courses }: { courses: LearningCourse[] }) {
  if (courses.length === 0) {
    return (
      <div className="rounded-none border border-dashed border-line bg-surface p-8 text-center">
        <h2 className="text-base font-semibold font-display tracking-wide text-bone">Nada por aqui ainda</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-slate-600">
          Assim que você começar a assistir às aulas, o seu progresso aparece nesta página.
        </p>
        <Link
          href="/cursos"
          className="mt-6 inline-block rounded-none bg-brand-600 px-5 py-3 text-sm font-semibold text-white font-mono uppercase tracking-[0.18em] hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
        >
          Ver catálogo de cursos
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold font-display tracking-wide text-bone">Seus cursos</h2>
      <ul className="mt-4 flex flex-col gap-4">
        {courses.map((course) => (
          <HistoryRow key={course.id} course={course} />
        ))}
      </ul>
    </div>
  );
}

function HistoryRow({ course }: { course: LearningCourse }) {
  const finished = course.completed;
  const started = course.completed_lessons > 0;

  return (
    <li className="rounded-none border border-line bg-surface p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          {course.category_name ? (
            <span className="eyebrow text-blood">
              {course.category_name}
            </span>
          ) : null}
          <h3 className="text-base font-semibold text-slate-900">{course.title}</h3>
          <p className="mt-1 text-xs text-slate-500">
            {course.completed_lessons} de {course.lessons_count} aulas · última atividade em{" "}
            {formatDate(course.last_activity_at)}
          </p>
        </div>

        <Link
          href={`/dashboard/cursos/${course.id}`}
          className="rounded-none bg-brand-600 px-4 py-2 text-sm font-semibold text-white font-mono uppercase tracking-[0.18em] hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
        >
          {finished ? "Revisar" : started ? "Continuar" : "Começar"}
        </Link>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between gap-4 text-xs text-slate-500">
          <span>{finished ? "Curso concluído" : `${course.progress_percent}% concluído`}</span>
          <span className={finished ? "font-semibold text-bone" : "font-semibold text-slate-700"}>
            {course.completed_lessons}/{course.lessons_count}
          </span>
        </div>
        <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-none bg-slate-200">
          <div
            className={`h-full rounded-none ${finished ? "bg-bone" : "bg-brand-600"}`}
            style={{ width: `${course.progress_percent}%` }}
          />
        </div>
      </div>
    </li>
  );
}

function HistorySkeleton() {
  return (
    <div className="flex flex-col gap-10" aria-hidden>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="rounded-none border border-line bg-surface p-5">
            <div className="h-3 w-24 animate-pulse rounded bg-slate-200" />
            <div className="mt-3 h-6 w-16 animate-pulse rounded bg-slate-200" />
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-4">
        {Array.from({ length: 3 }, (_, index) => (
          <div key={index} className="rounded-none border border-line bg-surface p-5">
            <div className="h-3 w-20 animate-pulse rounded bg-slate-200" />
            <div className="mt-2 h-4 w-1/2 animate-pulse rounded bg-slate-200" />
            <div className="mt-4 h-1.5 w-full animate-pulse rounded bg-slate-200" />
          </div>
        ))}
      </div>
    </div>
  );
}
