"use client";

/**
 * Gestão de categorias (ADMIN): listar, criar, editar e remover.
 *
 * Depende de `GET/POST/PATCH/DELETE /categories`. O backend recusa remover uma
 * categoria que ainda tenha cursos vinculados (devolve 409).
 */

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { StatusBadge } from "@/components/admin/status-badge";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { SelectField, TextAreaField } from "@/components/ui/field";
import { TextInput } from "@/components/ui/text-input";
import { useAuth } from "@/contexts/auth-context";
import { ApiError, describeApiError } from "@/lib/api";
import {
  createCategory,
  deleteCategory,
  fetchCategories,
  updateCategory,
} from "@/services/admin-service";
import type { Category, CategoryStatus } from "@/types/api";

interface FormState {
  name: string;
  description: string;
  status: CategoryStatus;
}

const EMPTY_FORM: FormState = { name: "", description: "", status: "ACTIVE" };

export function CategoriesContent() {
  const { getIdToken } = useAuth();
  const [categories, setCategories] = useState<Category[] | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getIdToken()
      .then((token) => {
        if (!token) {
          throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
        }
        return fetchCategories(token);
      })
      .then((result) => {
        if (active) {
          setCategories(result);
          setFailure(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setCategories(null);
        setFailure(describeApiError(error, "Não foi possível carregar as categorias."));
      });
    return () => {
      active = false;
    };
  }, [getIdToken, reloadKey]);

  const reload = useCallback(() => setReloadKey((key) => key + 1), []);

  const closeForm = useCallback(() => {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormOpen(false);
    setActionError(null);
  }, []);

  function startCreate() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormOpen(true);
    setActionError(null);
  }

  function startEdit(category: Category) {
    setForm({
      name: category.name,
      description: category.description ?? "",
      status: category.status,
    });
    setEditingId(category.id);
    setFormOpen(true);
    setActionError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);

    const name = form.name.trim();
    if (!name) {
      setActionError("Informe o nome da categoria.");
      return;
    }

    setSaving(true);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      const payload = {
        name,
        description: form.description.trim() || null,
        status: form.status,
      };
      if (editingId === null) {
        await createCategory(token, payload);
      } else {
        await updateCategory(token, editingId, payload);
      }
      closeForm();
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível salvar a categoria."));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(category: Category) {
    if (!window.confirm(`Remover a categoria "${category.name}"?`)) {
      return;
    }
    setActionError(null);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      await deleteCategory(token, category.id);
      if (editingId === category.id) {
        closeForm();
      }
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível remover a categoria."));
    }
  }

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold font-display tracking-wide text-bone">Categorias</h2>
          <p className="mt-1 text-sm text-slate-600">
            Cada curso pertence a uma categoria. Categorias inativas saem da vitrine.
          </p>
        </div>
        <Button type="button" onClick={startCreate}>
          Nova categoria
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
        <form
          onSubmit={handleSubmit}
          className="mt-6 flex flex-col gap-4 rounded-none border border-line bg-surface p-5"
        >
          <h3 className="text-sm font-semibold text-slate-900">
            {editingId === null ? "Nova categoria" : "Editar categoria"}
          </h3>
          <TextInput
            id="category-name"
            label="Nome"
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            maxLength={120}
            required
          />
          <TextAreaField
            id="category-description"
            label="Descrição"
            rows={3}
            value={form.description}
            onChange={(event) =>
              setForm((current) => ({ ...current, description: event.target.value }))
            }
          />
          <SelectField
            id="category-status"
            label="Situação"
            value={form.status}
            onChange={(event) =>
              setForm((current) => ({ ...current, status: event.target.value as CategoryStatus }))
            }
          >
            <option value="ACTIVE">Ativa</option>
            <option value="INACTIVE">Inativa</option>
          </SelectField>
          <div className="flex gap-3">
            <Button type="submit" loading={saving}>
              {editingId === null ? "Criar categoria" : "Salvar alterações"}
            </Button>
            <Button type="button" variant="secondary" onClick={closeForm} disabled={saving}>
              Cancelar
            </Button>
          </div>
        </form>
      ) : null}

      <div className="mt-6">
        {failure ? (
          <Alert tone="warning" title="Não foi possível carregar as categorias">
            {failure}
          </Alert>
        ) : categories === null ? (
          <div className="h-40 animate-pulse rounded-none bg-slate-200" aria-busy />
        ) : categories.length === 0 ? (
          <p className="rounded-none border border-dashed border-line bg-surface p-5 text-sm text-slate-600">
            Nenhuma categoria cadastrada ainda. Crie a primeira para poder organizar os cursos.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-none border border-line bg-surface">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Nome
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
                {categories.map((category) => (
                  <tr key={category.id}>
                    <td className="px-4 py-3">
                      <span className="font-medium text-slate-900">{category.name}</span>
                      {category.description ? (
                        <span className="mt-0.5 block text-xs text-slate-500">
                          {category.description}
                        </span>
                      ) : null}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={category.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <Button type="button" variant="secondary" onClick={() => startEdit(category)}>
                          Editar
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => handleDelete(category)}
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
