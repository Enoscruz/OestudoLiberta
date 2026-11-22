/**
 * Chamadas da área do aluno ao backend.
 *
 * Todas exigem autenticação: o backend confere a matrícula antes de liberar o
 * curso, emitir as URLs de reprodução ou aceitar progresso.
 */

import { apiFetch } from "@/lib/api";
import type {
  LearningHistory,
  LessonPlayback,
  LessonProgress,
  LessonProgressPayload,
  MyCourse,
  MyCourseDetail,
} from "@/types/api";

export function fetchMyCourses(token: string): Promise<MyCourse[]> {
  return apiFetch<MyCourse[]>("/me/courses", { token });
}

export function fetchMyCourse(token: string, courseId: string): Promise<MyCourseDetail> {
  return apiFetch<MyCourseDetail>(`/me/courses/${encodeURIComponent(courseId)}`, { token });
}

export function fetchLessonPlayback(token: string, lessonId: number): Promise<LessonPlayback> {
  return apiFetch<LessonPlayback>(`/me/lessons/${lessonId}/playback`, { token });
}

/** Registra o progresso do aluno em uma aula (o backend limita à duração real). */
export function saveLessonProgress(
  token: string,
  lessonId: number,
  payload: LessonProgressPayload,
): Promise<LessonProgress> {
  return apiFetch<LessonProgress>(`/me/lessons/${lessonId}/progress`, {
    method: "PUT",
    token,
    body: payload,
  });
}

/** Indicadores e histórico de aprendizagem do aluno. */
export function fetchLearningHistory(token: string): Promise<LearningHistory> {
  return apiFetch<LearningHistory>("/me/history", { token });
}
