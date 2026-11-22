"use client";

/**
 * Painel do aluno: lista os cursos liberados pelo backend (`GET /me/courses`).
 *
 * A lista depende de uma matrícula ativa, que só existe depois do pagamento
 * aprovado (SPRINT 4). Sem matrículas, a tela mostra um estado vazio.
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { MyCourseGrid, MyCoursesEmpty } from "@/components/learning/my-course-card";
import { Alert } from "@/components/ui/alert";
import { useAuth } from "@/contexts/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { ApiError } from "@/lib/api";
import { fetchMyCourses } from "@/services/learning-service";
import type { MyCourse } from "@/types/api";

interface LoadFailure {
  message: string;
  /** O backend recusou o acesso (e-mail não confirmado). */
  forbidden: boolean;
}

export function DashboardContent() {
  const { ready } = useRequireAuth();
  const { user, getIdToken } = useAuth();
  const [courses, setCourses] = useState<MyCourse[] | null>(null);
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
        return fetchMyCourses(token);
      })
      .then((result) => {
        if (active) {
          setCourses(result);
          setFailure(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setCourses(null);
        setFailure(
          error instanceof ApiError
            ? { message: error.message, forbidden: error.status === 403 }
            : { message: "Não foi possível carregar seus cursos agora.", forbidden: false },
        );
      });

    return () => {
      active = false;
    };
  }, [ready, getIdToken, reloadKey]);

  const reload = useCallback(() => {
    setFailure(null);
    setCourses(null);
    setReloadKey((key) => key + 1);
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-12">
      <header>
        <h1 className="text-3xl font-bold font-display tracking-wide text-bone">Meus cursos</h1>
        <p className="mt-2 text-slate-600">
          {user ? `${user.name}, aqui` : "Aqui"} ficam os cursos que você já tem acesso.
        </p>
      </header>

      <section className="mt-8">
        {failure ? (
          <div className="flex flex-col gap-4">
            <Alert tone="warning" title="Não foi possível carregar seus cursos">
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
        ) : courses === null ? (
          <DashboardSkeleton />
        ) : courses.length > 0 ? (
          <MyCourseGrid courses={courses} />
        ) : (
          <MyCoursesEmpty />
        )}
      </section>
    </main>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" aria-hidden>
      {Array.from({ length: 3 }, (_, index) => (
        <div key={index} className="overflow-hidden rounded-none border border-line bg-surface">
          <div className="h-40 w-full animate-pulse bg-slate-200" />
          <div className="flex flex-col gap-3 p-5">
            <div className="h-3 w-20 animate-pulse rounded bg-slate-200" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-200" />
          </div>
        </div>
      ))}
    </div>
  );
}
