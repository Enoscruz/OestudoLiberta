/**
 * Tipos compartilhados da API do backend (contratos em `backend/app/schemas`).
 */

export type RoleName = "ADMIN" | "STUDENT";

export type UserStatus = "ACTIVE" | "INACTIVE" | "BLOCKED";

export type CategoryStatus = "ACTIVE" | "INACTIVE";

export type CourseStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export type LessonStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export interface Role {
  id: number;
  name: RoleName;
  description: string | null;
}

export interface User {
  id: number;
  name: string;
  email: string;
  status: UserStatus;
  email_verified: boolean;
  role: Role;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
  status: CategoryStatus;
  created_at: string;
}

export interface Course {
  id: number;
  category_id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  price: string;
  status: CourseStatus;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Lesson {
  id: number;
  course_id: number;
  title: string;
  description: string | null;
  video_uid: string | null;
  duration_seconds: number | null;
  lesson_order: number;
  status: LessonStatus;
  material_url: string | null;
  created_at: string;
}

export interface LessonVideoUpload {
  lesson_id: number;
  video_uid: string;
  upload_url: string;
  max_duration_seconds: number;
}

/** Categoria ativa exibida na vitrine pública. */
export interface CatalogCategory {
  id: number;
  name: string;
  description: string | null;
}

/** Aula publicada exibida no currículo do curso. */
export interface CatalogLesson {
  id: number;
  title: string;
  description: string | null;
  lesson_order: number;
  duration_seconds: number | null;
}

/** Curso publicado exibido na listagem do catálogo. */
export interface CatalogCourse {
  id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  price: string;
  category_id: number;
  category_name: string | null;
  lessons_count: number;
  published_at: string | null;
}

/** Curso publicado com o currículo completo. */
export interface CatalogCourseDetail extends CatalogCourse {
  lessons: CatalogLesson[];
}

/** Aula liberada para o aluno (área "meus cursos"). */
export interface MyLesson {
  id: number;
  title: string;
  description: string | null;
  lesson_order: number;
  duration_seconds: number | null;
  material_url: string | null;
  progress_seconds: number;
  completed: boolean;
}

/** Curso ao qual o aluno tem acesso liberado. */
export interface MyCourse {
  id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  category_name: string | null;
  lessons_count: number;
  granted_at: string;
  completed_lessons: number;
  progress_percent: number;
}

/** Curso liberado com o currículo de aulas publicadas. */
export interface MyCourseDetail extends MyCourse {
  lessons: MyLesson[];
}

/** URLs assinadas para reproduzir uma aula. */
export interface LessonPlayback {
  lesson_id: number;
  title: string;
  iframe_url: string;
  hls_url: string;
  expires_at: string;
}

/** Corpo enviado ao registrar o progresso de uma aula. */
export interface LessonProgressPayload {
  progress_seconds: number;
  completed: boolean;
}

/** Progresso registrado em uma aula. */
export interface LessonProgress {
  lesson_id: number;
  progress_seconds: number;
  completed: boolean;
  completed_at: string | null;
  updated_at: string;
}

/** Indicadores gerais de aprendizagem. */
export interface LearningSummary {
  courses_owned: number;
  courses_completed: number;
  lessons_completed: number;
  lessons_available: number;
  watched_seconds: number;
}

/** Um curso no histórico de aprendizagem. */
export interface LearningCourse {
  id: number;
  title: string;
  cover_image: string | null;
  category_name: string | null;
  lessons_count: number;
  completed_lessons: number;
  progress_percent: number;
  completed: boolean;
  last_activity_at: string | null;
}

/** Histórico de aprendizagem: indicadores + cursos. */
export interface LearningHistory {
  summary: LearningSummary;
  courses: LearningCourse[];
}

/** Corpo aceito ao criar/atualizar uma categoria (ADMIN). */
export interface CategoryPayload {
  name: string;
  description: string | null;
  status: CategoryStatus;
}

/** Corpo aceito ao atualizar uma categoria (campos opcionais). */
export type CategoryUpdatePayload = Partial<CategoryPayload>;

/** Corpo aceito ao criar/atualizar um curso (ADMIN). */
export interface CoursePayload {
  category_id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  price: string;
}

/** Corpo aceito ao atualizar um curso (campos opcionais). */
export type CourseUpdatePayload = Partial<CoursePayload>;

/** Corpo aceito ao criar uma aula (ADMIN). */
export interface LessonPayload {
  course_id: number;
  title: string;
  description: string | null;
  lesson_order: number | null;
  duration_seconds: number | null;
  material_url: string | null;
  status: LessonStatus;
}

/** Corpo aceito ao atualizar uma aula (sem trocar de curso). */
export type LessonUpdatePayload = Omit<LessonPayload, "course_id">;

export type PurchaseStatus = "PENDING" | "PAID" | "FAILED" | "CANCELED" | "REFUNDED";

/**
 * Resultado de um pedido de compra (`POST /purchases`).
 *
 * Quando `requires_payment` é `false` (curso gratuito) o acesso já foi
 * liberado e `init_point` vem nulo — não há checkout a abrir.
 */
export interface CheckoutSession {
  purchase_id: number;
  status: PurchaseStatus;
  amount: string;
  init_point: string | null;
  requires_payment: boolean;
}
