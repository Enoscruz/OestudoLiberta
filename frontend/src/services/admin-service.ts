/**
 * Chamadas da área administrativa ao backend.
 *
 * Todas exigem sessão de ADMIN: o backend recusa qualquer requisição sem esse
 * papel. O frontend apenas esconde a interface — a autorização real é do
 * servidor, que revalida cada chamada.
 */

import { apiFetch } from "@/lib/api";
import type {
  Category,
  CategoryPayload,
  CategoryUpdatePayload,
  Course,
  CoursePayload,
  CourseStatus,
  CourseUpdatePayload,
  Lesson,
  LessonPayload,
  LessonUpdatePayload,
  LessonVideoUpload,
} from "@/types/api";

// ── Categorias ──────────────────────────────────────────────

export function fetchCategories(token: string): Promise<Category[]> {
  return apiFetch<Category[]>("/categories", { token });
}

export function createCategory(token: string, payload: CategoryPayload): Promise<Category> {
  return apiFetch<Category>("/categories", { method: "POST", token, body: payload });
}

export function updateCategory(
  token: string,
  categoryId: number,
  payload: CategoryUpdatePayload,
): Promise<Category> {
  return apiFetch<Category>(`/categories/${categoryId}`, {
    method: "PATCH",
    token,
    body: payload,
  });
}

export function deleteCategory(token: string, categoryId: number): Promise<void> {
  return apiFetch<void>(`/categories/${categoryId}`, { method: "DELETE", token });
}

// ── Cursos ──────────────────────────────────────────────────

export function fetchCourses(token: string, status?: CourseStatus): Promise<Course[]> {
  const query = status ? `?status=${status}` : "";
  return apiFetch<Course[]>(`/courses${query}`, { token });
}

export function fetchCourse(token: string, courseId: string): Promise<Course> {
  return apiFetch<Course>(`/courses/${encodeURIComponent(courseId)}`, { token });
}

export function createCourse(token: string, payload: CoursePayload): Promise<Course> {
  return apiFetch<Course>("/courses", { method: "POST", token, body: payload });
}

export function updateCourse(
  token: string,
  courseId: number,
  payload: CourseUpdatePayload,
): Promise<Course> {
  return apiFetch<Course>(`/courses/${courseId}`, { method: "PATCH", token, body: payload });
}

export function publishCourse(token: string, courseId: number): Promise<Course> {
  return apiFetch<Course>(`/courses/${courseId}/publish`, { method: "POST", token });
}

export function unpublishCourse(token: string, courseId: number): Promise<Course> {
  return apiFetch<Course>(`/courses/${courseId}/unpublish`, { method: "POST", token });
}

export function deleteCourse(token: string, courseId: number): Promise<void> {
  return apiFetch<void>(`/courses/${courseId}`, { method: "DELETE", token });
}

// ── Aulas ───────────────────────────────────────────────────

export function fetchLessons(token: string, courseId: number): Promise<Lesson[]> {
  return apiFetch<Lesson[]>(`/lessons?course_id=${courseId}`, { token });
}

export function createLesson(token: string, payload: LessonPayload): Promise<Lesson> {
  return apiFetch<Lesson>("/lessons", { method: "POST", token, body: payload });
}

export function updateLesson(
  token: string,
  lessonId: number,
  payload: LessonUpdatePayload,
): Promise<Lesson> {
  return apiFetch<Lesson>(`/lessons/${lessonId}`, { method: "PATCH", token, body: payload });
}

export function deleteLesson(token: string, lessonId: number): Promise<void> {
  return apiFetch<void>(`/lessons/${lessonId}`, { method: "DELETE", token });
}

/** Negocia o upload direto do vídeo e associa o `uid` à aula. */
export function requestVideoUpload(token: string, lessonId: number): Promise<LessonVideoUpload> {
  return apiFetch<LessonVideoUpload>(`/lessons/${lessonId}/video-upload`, {
    method: "POST",
    token,
  });
}
