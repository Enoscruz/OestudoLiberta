"use client";

/**
 * Gestão do catálogo de cursos (ADMIN): listar, criar, publicar/despublicar e
 * remover. A edição completa (inclusive das aulas) fica na página do curso.
 *
 * Publicar exige ao menos uma aula publicada — o backend devolve 422 caso
 * contrário, e a mensagem é repassada ao administrador.
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
import { formatPrice } from "@/lib/format";
import {
  createCourse,
  deleteCourse,
  fetchCategories,
  fetchCourses,
  publishCourse,
  unpublishCourse,
} from "@/services/admin-service";
import type { Category, Course, CourseStatus } from "@/types/api";

interface FormState {
  categoryId: string;
  title: string;
  description: string;
  coverImage: string;
  price: string;
}

const EMPTY_FORM: FormState = {
  categoryId: "",
  title: "",
  description: "",
  coverImage: "",
  price: "0",
};

const STATUS_FILTERS: { value: "" | CourseStatus; label: string }[] = [
  { value: "", label: "Todos" },
  { value: "DRAFT", label: "Rascunhos" },
  { value: "PUBLISHED", label: "Publicados" },
  { value: "ARCHIVED", label: "Arquivados" },
];

export function CoursesContent() {
  const { getIdToken } = useAuth();
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [failure, setFailure] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [statusFilter, setStatusFilter] = useState<"" | CourseStatus>("");

  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getIdToken()
      .then(async (token) => {
        if (!token) {
          throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
        }
        const [courseList, categoryList] = await Promise.all([
          fetchCourses(token, statusFilter || undefined),
          fetchCategories(token),
        ]);
        return { courseList, categoryList };
      })
      .then(({ courseList, categoryList }) => {
        if (active) {
          setCourses(courseList);
          setCategories(categoryList);
          setFailure(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setCourses(null);
        setFailure(describeApiError(error, "Não foi possível carregar os cursos."));
      });
    return () => {
      active = false;
    };
  }, [getIdToken, reloadKey, statusFilter]);

  const reload = useCallback(() => setReloadKey((key) => key + 1), []);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);

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
      await createCourse(token, {
        category_id: Number(form.categoryId),
        title,
        description: form.description.trim() || null,
        cover_image: form.coverImage.trim() || null,
        price: form.price.trim() || "0",
      });
      setForm(EMPTY_FORM);
      setFormOpen(false);
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível criar o curso."));
    } finally {
      setSaving(false);
    }
  }

  async function togglePublish(course: Course) {
    setActionError(null);
    setBusyId(course.id);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      if (course.status === "PUBLISHED") {
        await unpublishCourse(token, course.id);
      } else {
        await publishCourse(token, course.id);
      }
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível alterar a publicação do curso."));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(course: Course) {
    if (!window.confirm(`Remover o curso "${course.title}" e todas as suas aulas?`)) {
      return;
    }
    setActionError(null);
    setBusyId(course.id);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      await deleteCourse(token, course.id);
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível remover o curso."));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold font-display tracking-wide text-bone">Cursos</h2>
          <p className="mt-1 text-sm text-slate-600">
            Crie o curso em rascunho, monte as aulas e publique quando estiver pronto.
          </p>
        </div>
        <Button
          type="button"
          onClick={() => {
            setForm(EMPTY_FORM);
            setFormOpen((open) => !open);
            setActionError(null);
          }}
        >
          Novo curso
        </Button>
      </div>

      {actionError ? (
        <div className="mt-6">
          <Alert tone="error" title="Ação não concluída">
            {actionError}
          </Alert>
        </div>
      ) : null}

      {formOpen ? (
        categories.length === 0 ? (
          <div className="mt-6">
            <Alert tone="info" title="Crie uma categoria primeiro">
              Todo curso precisa de uma categoria.{" "}
              <Link href="/admin/categorias" className="font-semibold underline">
                Ir para categorias
              </Link>
              .
            </Alert>
          </div>
        ) : (
          <form
            onSubmit={handleCreate}
            className="mt-6 flex flex-col gap-4 rounded-none border border-line bg-surface p-5"
          >
            <h3 className="text-sm font-semibold text-slate-900">Novo curso</h3>
            <SelectField
              id="course-category"
              label="Categoria"
              value={form.categoryId}
              onChange={(event) =>
                setForm((current) => ({ ...current, categoryId: event.target.value }))
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
              id="course-title"
              label="Título"
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              maxLength={200}
              required
            />
            <TextAreaField
              id="course-description"
              label="Descrição"
              rows={3}
              value={form.description}
              onChange={(event) =>
                setForm((current) => ({ ...current, description: event.target.value }))
              }
            />
            <TextInput
              id="course-cover"
              label="Imagem de capa (URL)"
              type="url"
              value={form.coverImage}
              onChange={(event) =>
                setForm((current) => ({ ...current, coverImage: event.target.value }))
              }
              placeholder="https://…"
            />
            <TextInput
              id="course-price"
              label="Preço (R$)"
              type="number"
              min="0"
              step="0.01"
              value={form.price}
              onChange={(event) => setForm((current) => ({ ...current, price: event.target.value }))}
            />
            <div className="flex gap-3">
              <Button type="submit" loading={saving}>
                Criar curso
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setFormOpen(false)}
                disabled={saving}
              >
                Cancelar
              </Button>
            </div>
          </form>
        )
      ) : null}

      <div className="mt-6 flex items-center gap-3">
        <label htmlFor="course-status-filter" className="text-sm font-medium text-slate-700">
          Filtrar por situação
        </label>
        <select
          id="course-status-filter"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as "" | CourseStatus)}
          className="rounded-none border border-slate-300 bg-surface px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 focus:outline-none"
        >
          {STATUS_FILTERS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-4">
        {failure ? (
          <Alert tone="warning" title="Não foi possível carregar os cursos">
            {failure}
          </Alert>
        ) : courses === null ? (
          <div className="h-40 animate-pulse rounded-none bg-slate-200" aria-busy />
        ) : courses.length === 0 ? (
          <p className="rounded-none border border-dashed border-line bg-surface p-5 text-sm text-slate-600">
            Nenhum curso neste filtro. Crie um novo curso para começar.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-none border border-line bg-surface">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Curso
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Preço
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Situação
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {courses.map((course) => (
                  <tr key={course.id}>
                    <td className="px-4 py-3">
                      <Link
                        href={`/admin/cursos/${course.id}`}
                        className="font-medium text-slate-900 hover:text-blood-bright"
                      >
                        {course.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatPrice(course.price)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={course.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Link
                          href={`/admin/cursos/${course.id}`}
                          className="inline-flex items-center justify-center rounded-none bg-surface px-4 py-2.5 text-sm font-semibold text-slate-900 ring-1 ring-slate-300 ring-inset hover:bg-slate-100"
                        >
                          Gerenciar
                        </Link>
                        <Button
                          type="button"
                          variant="secondary"
                          onClick={() => togglePublish(course)}
                          loading={busyId === course.id}
                        >
                          {course.status === "PUBLISHED" ? "Despublicar" : "Publicar"}
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => handleDelete(course)}
                          disabled={busyId === course.id}
                        >
                          Remover
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
