"use client";

/**
 * Player do aluno: lista as aulas publicadas do curso e reproduz a selecionada.
 *
 * O vídeo nunca é público — as URLs vêm de `GET /me/lessons/{id}/playback`, que
 * valida a matrícula e emite um token temporário da Cloudflare Stream.
 *
 * O progresso (SPRINT 5) é enviado ao backend a cada 15 segundos de tempo
 * assistido. Como o vídeo roda em um iframe de outro domínio, o player não lê o
 * `currentTime`: o tempo é medido pelo relógio da aba enquanto ela está visível,
 * e quem decide a conclusão da aula é o backend (ver docs, seção 3.11).
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { ApiError } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import {
  fetchLessonPlayback,
  fetchMyCourse,
  saveLessonProgress,
} from "@/services/learning-service";
import type { LessonPlayback, MyCourseDetail } from "@/types/api";

/** Intervalo entre dois registros de tempo assistido. */
const HEARTBEAT_SECONDS = 15;

interface LoadFailure {
  message: string;
  status: number;
}

/** Progresso conhecido de uma aula. */
interface LessonProgressState {
  progress_seconds: number;
  completed: boolean;
}

export function PlayerContent({ courseId }: { courseId: string }) {
  const { ready } = useRequireAuth();
  const { getIdToken } = useAuth();
  const [course, setCourse] = useState<MyCourseDetail | null>(null);
  const [failure, setFailure] = useState<LoadFailure | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [progress, setProgress] = useState<Record<number, LessonProgressState>>({});
  const [savingLessonId, setSavingLessonId] = useState<number | null>(null);
  const [progressNotice, setProgressNotice] = useState<string | null>(null);

  // Guarda o resultado (ou o erro) junto do id da aula: assim o estado de
  // "carregando" é derivado e não exige um `setState` síncrono no efeito.
  const [playback, setPlayback] = useState<{ lessonId: number; data: LessonPlayback } | null>(
    null,
  );
  const [playbackError, setPlaybackError] = useState<{
    lessonId: number;
    message: string;
  } | null>(null);

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
        return fetchMyCourse(token, courseId);
      })
      .then((detail) => {
        if (!active) {
          return;
        }
        setCourse(detail);
        setProgress(
          Object.fromEntries(
            detail.lessons.map((lesson) => [
              lesson.id,
              { progress_seconds: lesson.progress_seconds, completed: lesson.completed },
            ]),
          ),
        );
        // Continuidade: retoma na primeira aula ainda não concluída.
        setSelectedLessonId(
          detail.lessons.find((lesson) => !lesson.completed)?.id ??
            detail.lessons[0]?.id ??
            null,
        );
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setCourse(null);
        setFailure(
          error instanceof ApiError
            ? { message: error.message, status: error.status }
            : { message: "Não foi possível carregar o curso agora.", status: 0 },
        );
      });

    return () => {
      active = false;
    };
  }, [ready, getIdToken, courseId, reloadKey]);

  useEffect(() => {
    if (selectedLessonId === null) {
      return;
    }

    const lessonId = selectedLessonId;
    let active = true;
    getIdToken()
      .then((token) => {
        if (!token) {
          throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
        }
        return fetchLessonPlayback(token, lessonId);
      })
      .then((data) => {
        if (active) {
          setPlayback({ lessonId, data });
          setPlaybackError(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setPlayback(null);
        setPlaybackError({
          lessonId,
          message:
            error instanceof ApiError
              ? error.message
              : "Não foi possível preparar este vídeo agora.",
        });
      });

    return () => {
      active = false;
    };
  }, [selectedLessonId, getIdToken]);

  // Tempo assistido: registra a cada 15 s, apenas com a aba visível e enquanto
  // a aula não estiver concluída.
  useEffect(() => {
    if (!ready || selectedLessonId === null || playback?.lessonId !== selectedLessonId) {
      return;
    }
    if (progress[selectedLessonId]?.completed) {
      return;
    }

    const lessonId = selectedLessonId;
    let sent = progress[lessonId]?.progress_seconds ?? 0;
    let active = true;

    const timer = window.setInterval(() => {
      if (document.visibilityState !== "visible") {
        return;
      }
      sent += HEARTBEAT_SECONDS;
      getIdToken()
        .then((token) => {
          if (!token) {
            return null;
          }
          return saveLessonProgress(token, lessonId, {
            progress_seconds: sent,
            completed: false,
          });
        })
        .then((saved) => {
          if (active && saved) {
            setProgress((previous) => ({
              ...previous,
              [saved.lesson_id]: {
                progress_seconds: saved.progress_seconds,
                completed: saved.completed,
              },
            }));
          }
        })
        .catch(() => {
          // Registrar progresso é conveniência: uma falha não interrompe a aula.
        });
    }, HEARTBEAT_SECONDS * 1000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [ready, selectedLessonId, playback, getIdToken, progress]);

  const completeLesson = useCallback(
    (lessonId: number, durationSeconds: number | null) => {
      setProgressNotice(null);
      setSavingLessonId(lessonId);
      getIdToken()
        .then((token) => {
          if (!token) {
            throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
          }
          return saveLessonProgress(token, lessonId, {
            progress_seconds: durationSeconds ?? progress[lessonId]?.progress_seconds ?? 0,
            completed: true,
          });
        })
        .then((saved) => {
          setProgress((previous) => ({
            ...previous,
            [saved.lesson_id]: {
              progress_seconds: saved.progress_seconds,
              completed: saved.completed,
            },
          }));
        })
        .catch((error: unknown) => {
          setProgressNotice(
            error instanceof ApiError
              ? error.message
              : "Não foi possível salvar seu progresso agora.",
          );
        })
        .finally(() => {
          setSavingLessonId(null);
        });
    },
    [getIdToken, progress],
  );

  const retry = useCallback(() => {
    setFailure(null);
    setCourse(null);
    setSelectedLessonId(null);
    setPlayback(null);
    setPlaybackError(null);
    setProgress({});
    setProgressNotice(null);
    setReloadKey((key) => key + 1);
  }, []);

  if (failure) {
    return (
      <main className="mx-auto w-full max-w-3xl px-4 py-12">
        <Alert tone="warning" title="Curso indisponível">
          {failure.message}
        </Alert>
        <div className="mt-6 flex flex-wrap gap-5">
          {failure.status === 403 ? (
            <Link
              href="/cursos"
              className="text-sm font-semibold text-brand-600 hover:text-blood-bright"
            >
              Ver cursos disponíveis →
            </Link>
          ) : (
            <button
              type="button"
              onClick={retry}
              className="text-sm font-semibold text-brand-600 hover:text-blood-bright"
            >
              Tentar novamente
            </button>
          )}
          <Link
            href="/dashboard"
            className="text-sm font-semibold text-slate-600 hover:text-slate-900"
          >
            ← Meus cursos
          </Link>
        </div>
      </main>
    );
  }

  if (!course) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 py-12" aria-busy>
        <div className="h-4 w-40 animate-pulse rounded bg-slate-200" />
        <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="aspect-video w-full animate-pulse rounded-none bg-slate-200" />
          <div className="h-64 animate-pulse rounded-none bg-slate-200" />
        </div>
      </main>
    );
  }

  const currentPlayback = playback?.lessonId === selectedLessonId ? playback.data : null;
  const currentError = playbackError?.lessonId === selectedLessonId ? playbackError.message : null;
  const playbackLoading =
    selectedLessonId !== null && currentPlayback === null && currentError === null;
  const selectedLesson =
    course.lessons.find((lesson) => lesson.id === selectedLessonId) ?? null;
  const selectedProgress = selectedLessonId === null ? null : progress[selectedLessonId];
  const lessonsCount = course.lessons.length;
  const completedCount = course.lessons.filter((lesson) => progress[lesson.id]?.completed).length;
  const percent = lessonsCount > 0 ? Math.round((completedCount * 100) / lessonsCount) : 0;
  const watchedLabel = formatDuration(selectedProgress?.progress_seconds ?? 0);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-12">
      <Link href="/dashboard" className="text-sm font-medium text-brand-600 hover:text-blood-bright">
        ← Meus cursos
      </Link>

      <header className="mt-6">
        {course.category_name ? (
          <span className="eyebrow text-blood">
            {course.category_name}
          </span>
        ) : null}
        <h1 className="mt-2 text-3xl font-bold font-display tracking-wide text-bone">{course.title}</h1>

        {lessonsCount > 0 ? (
          <div className="mt-4 max-w-md">
            <div className="flex items-center justify-between text-sm text-slate-600">
              <span>
                {completedCount} de {lessonsCount}{" "}
                {lessonsCount === 1 ? "aula concluída" : "aulas concluídas"}
              </span>
              <span className="font-semibold text-slate-900">{percent}%</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-none bg-slate-200">
              <div
                className="h-full rounded-none bg-brand-600 transition-all"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        ) : null}
      </header>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <section aria-label="Reprodução da aula">
          <div className="overflow-hidden rounded-none border border-line bg-slate-900">
            {currentPlayback ? (
              <iframe
                src={currentPlayback.iframe_url}
                title={currentPlayback.title}
                allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture"
                allowFullScreen
                className="aspect-video w-full"
              />
            ) : (
              <div className="flex aspect-video w-full items-center justify-center px-6 text-center">
                <p className="text-sm text-slate-300">
                  {playbackLoading
                    ? "Preparando o vídeo..."
                    : "Selecione uma aula para começar."}
                </p>
              </div>
            )}
          </div>

          {currentError ? (
            <div className="mt-4">
              <Alert tone="warning" title="Vídeo indisponível">
                {currentError}
              </Alert>
            </div>
          ) : null}

          {selectedLesson ? (
            <div className="mt-6">
              <h2 className="text-lg font-semibold font-display tracking-wide text-bone">{selectedLesson.title}</h2>
              {selectedLesson.description ? (
                <p className="mt-2 text-sm text-slate-600">{selectedLesson.description}</p>
              ) : null}

              <div className="mt-4 flex flex-wrap items-center gap-4">
                {selectedProgress?.completed ? (
                  <span className="inline-flex items-center gap-2 rounded-none bg-surface-2 px-4 py-2.5 text-sm font-semibold text-bone">
                    <span aria-hidden>✓</span> Aula concluída
                  </span>
                ) : (
                  <Button
                    type="button"
                    variant="secondary"
                    loading={savingLessonId === selectedLesson.id}
                    onClick={() =>
                      completeLesson(selectedLesson.id, selectedLesson.duration_seconds)
                    }
                  >
                    Marcar aula como concluída
                  </Button>
                )}

                {watchedLabel && !selectedProgress?.completed ? (
                  <span className="text-sm text-slate-500">
                    {watchedLabel} assistidos nesta aula
                  </span>
                ) : null}
              </div>

              {progressNotice ? (
                <div className="mt-4">
                  <Alert tone="warning">{progressNotice}</Alert>
                </div>
              ) : null}

              {selectedLesson.material_url ? (
                <a
                  href={selectedLesson.material_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block text-sm font-semibold text-brand-600 hover:text-blood-bright"
                >
                  Baixar material da aula →
                </a>
              ) : null}
            </div>
          ) : null}
        </section>

        <aside aria-label="Aulas do curso">
          <h2 className="text-sm font-semibold font-display tracking-wide text-slate-500 uppercase">
            Aulas do curso
          </h2>

          {course.lessons.length > 0 ? (
            <ol className="mt-4 divide-y divide-slate-200 overflow-hidden rounded-none border border-line bg-surface">
              {course.lessons.map((lesson) => {
                const duration = formatDuration(lesson.duration_seconds);
                const active = lesson.id === selectedLessonId;
                const done = Boolean(progress[lesson.id]?.completed);
                return (
                  <li key={lesson.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedLessonId(lesson.id)}
                      aria-current={active ? "true" : undefined}
                      className={`flex w-full items-start gap-3 p-4 text-left transition ${
                        active ? "bg-brand-50" : "hover:bg-slate-100"
                      }`}
                    >
                      <span
                        className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-none text-xs font-semibold ${
                          done
                            ? "bg-bone text-white"
                            : active
                              ? "bg-brand-600 text-white"
                              : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {done ? "✓" : lesson.lesson_order}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-medium text-slate-900">
                          {lesson.title}
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-500">
                          {[
                            duration,
                            done ? "concluída" : formatDuration(progress[lesson.id]?.progress_seconds ?? 0),
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="mt-4 rounded-none border border-dashed border-line bg-surface p-5 text-sm text-slate-600">
              As aulas deste curso ainda estão sendo publicadas. Você será avisado quando o
              conteúdo estiver disponível.
            </p>
          )}

          <Link
            href="/dashboard/historico"
            className="mt-6 inline-block text-sm font-semibold text-brand-600 hover:text-blood-bright"
          >
            Ver meu histórico →
          </Link>
        </aside>
      </div>
    </main>
  );
}
