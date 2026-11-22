"use client";

/**
 * Editor de um curso (ADMIN): dados cadastrais, publicação e aulas.
 *
 * Carrega o curso e as categorias em paralelo; as aulas ficam a cargo do
 * `LessonManager`, que também exibe o estado do vídeo de cada aula.
 */

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { StatusBadge } from "@/components/admin/status-badge";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { SelectField, TextAreaField } from "@/components/ui/field";
import { TextInput } from "@/components/ui/text-input";
import { useAuth } from "@/contexts/auth-context";
import { ApiError, describeApiError } from "@/lib/api";
import { fetchCategories, fetchCourse, publishCourse, unpublishCourse, updateCourse } from "@/services/admin-service";
import type { Category, Course } from "@/types/api";

import { LessonManager } from "./lesson-manager";

interface FormState {
  categoryId: string;
  title: string;
  description: string;
  coverImage: string;
  price: string;
}

function toForm(course: Course): FormState {
  return {
    categoryId: String(course.category_id),
    title: course.title,
    description: course.description ?? "",
    coverImage: course.cover_image ?? "",
    price: course.price,
  };
}

export function CourseEditor({ courseId }: { courseId: string }) {
  const { getIdToken } = useAuth();
  const [course, setCourse] = useState<Course | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [failure, setFailure] = useState<{ message: string; status: number } | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [form, setForm] = useState<FormState | null>(null);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getIdToken()
      .then(async (token) => {
        if (!token) {
          throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
        }
        const [courseData, categoryList] = await Promise.all([
          fetchCourse(token, courseId),
          fetchCategories(token),
        ]);
        return { courseData, categoryList };
      })
      .then(({ courseData, categoryList }) => {
        if (!active) {
          return;
        }
        setCourse(courseData);
        setForm(toForm(courseData));
        setCategories(categoryList);
        setFailure(null);
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setCourse(null);
        setFailure({
          message: describeApiError(error, "Não foi possível carregar o curso."),
          status: error instanceof ApiError ? error.status : 0,
        });
      });
    return () => {
      active = false;
    };
  }, [getIdToken, courseId, reloadKey]);

  const retry = useCallback(() => {
    setFailure(null);
    setCourse(null);
    setForm(null);
    setReloadKey((key) => key + 1);
  }, []);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) {
      return;
    }
    setActionError(null);
    setActionMessage(null);

    const title = form.title.trim();
    if (!title) {
      setActionError("Informe o título do curso.");
      return;
    }
    if (!form.categoryId) {
      setActionError("Selecione a categoria do curso.");
      return;
    }

    setSaving(true);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      const updated = await updateCourse(token, Number(courseId), {
        category_id: Number(form.categoryId),
        title,
        description: form.description.trim() || null,
        cover_image: form.coverImage.trim() || null,
        price: form.price.trim() || "0",
      });
      setCourse(updated);
      setForm(toForm(updated));
      setActionMessage("Alterações salvas.");
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível salvar o curso."));
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish() {
    if (!course) {
      return;
    }
    setActionError(null);
    setActionMessage(null);
    setPublishing(true);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      const updated =
        course.status === "PUBLISHED"
          ? await unpublishCourse(token, course.id)
          : await publishCourse(token, course.id);
      setCourse(updated);
      setActionMessage(
        updated.status === "PUBLISHED"
          ? "Curso publicado na vitrine."
          : "Curso despublicado e devolvido a rascunho.",
      );
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível alterar a publicação do curso."));
    } finally {
      setPublishing(false);
    }
  }

  if (failure) {
    return (
      <section>
        <Alert tone="warning" title="Curso indisponível">
          {failure.message}
        </Alert>
        <div className="mt-6">
          {failure.status === 404 ? (
            <Link
              href="/admin/cursos"
              className="text-sm font-semibold text-brand-600 hover:text-blood-bright"
            >
              ← Voltar para a lista de cursos
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
        </div>
      </section>
    );
  }

  if (!course || !form) {
    return (
      <section aria-busy>
        <div className="h-8 w-56 animate-pulse rounded bg-slate-200" />
        <div className="mt-6 h-64 animate-pulse rounded-none bg-slate-200" />
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-8">
      <div>
        <Link
          href="/admin/cursos"
          className="text-sm font-medium text-brand-600 hover:text-blood-bright"
        >
          ← Cursos
        </Link>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold font-display tracking-wide text-bone">{course.title}</h2>
            <StatusBadge status={course.status} />
          </div>
          <Button
            type="button"
            variant={course.status === "PUBLISHED" ? "secondary" : "primary"}
            onClick={togglePublish}
            loading={publishing}
          >
            {course.status === "PUBLISHED" ? "Despublicar" : "Publicar curso"}
          </Button>
        </div>
        <p className="mt-1 text-sm text-slate-600">
          Publicar exige pelo menos uma aula publicada.
        </p>
      </div>

      {actionError ? (
        <Alert tone="error" title="Ação não concluída">
          {actionError}
        </Alert>
      ) : null}
      {actionMessage ? (
        <Alert tone="success" title="Tudo certo">
          {actionMessage}
        </Alert>
      ) : null}

      <form
        onSubmit={handleSave}
        className="flex flex-col gap-4 rounded-none border border-line bg-surface p-5"
      >
        <h3 className="text-sm font-semibold text-slate-900">Dados do curso</h3>
        <SelectField
          id="edit-course-category"
          label="Categoria"
          value={form.categoryId}
          onChange={(event) =>
            setForm((current) => (current ? { ...current, categoryId: event.target.value } : current))
          }
          required
        >
          <option value="">Selecione…</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </SelectField>
        <TextInput
          id="edit-course-title"
          label="Título"
          value={form.title}
          onChange={(event) =>
            setForm((current) => (current ? { ...current, title: event.target.value } : current))
          }
          maxLength={200}
          required
        />
        <TextAreaField
          id="edit-course-description"
          label="Descrição"
          rows={3}
          value={form.description}
          onChange={(event) =>
            setForm((current) =>
              current ? { ...current, description: event.target.value } : current,
            )
          }
        />
        <TextInput
          id="edit-course-cover"
          label="Imagem de capa (URL)"
          type="url"
          value={form.coverImage}
          onChange={(event) =>
            setForm((current) => (current ? { ...current, coverImage: event.target.value } : current))
          }
          placeholder="https://…"
        />
        <TextInput
          id="edit-course-price"
          label="Preço (R$)"
          type="number"
          min="0"
          step="0.01"
          value={form.price}
          onChange={(event) =>
            setForm((current) => (current ? { ...current, price: event.target.value } : current))
          }
        />
        <div>
          <Button type="submit" loading={saving}>
            Salvar alterações
          </Button>
        </div>
      </form>

      <LessonManager courseId={course.id} />
    </section>
  );
}
