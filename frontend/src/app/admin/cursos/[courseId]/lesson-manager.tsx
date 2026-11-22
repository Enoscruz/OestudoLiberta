"use client";

/**
 * Gestão das aulas de um curso (ADMIN): criar, editar, ordenar, remover e
 * enviar o vídeo de cada aula.
 *
 * O vídeo nunca passa pelo backend: `POST /lessons/{id}/video-upload` negocia
 * uma URL de uso único e o arquivo é enviado direto para a Cloudflare Stream.
 */

import { Fragment, useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import { StatusBadge } from "@/components/admin/status-badge";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { SelectField, TextAreaField } from "@/components/ui/field";
import { TextInput } from "@/components/ui/text-input";
import { useAuth } from "@/contexts/auth-context";
import { ApiError, describeApiError } from "@/lib/api";
import { uploadVideoToCloudflare } from "@/lib/cloudflare-upload";
import { formatDuration } from "@/lib/format";
import {
  createLesson,
  deleteLesson,
  fetchLessons,
  requestVideoUpload,
  updateLesson,
} from "@/services/admin-service";
import type { Lesson, LessonStatus } from "@/types/api";

// O backend limita cada aula a 15 minutos.
const MAX_LESSON_MINUTES = 15;

interface FormState {
  title: string;
  description: string;
  order: string;
  durationMinutes: string;
  materialUrl: string;
  status: LessonStatus;
}

const EMPTY_FORM: FormState = {
  title: "",
  description: "",
  order: "",
  durationMinutes: "",
  materialUrl: "",
  status: "DRAFT",
};

export function LessonManager({ courseId }: { courseId: number }) {
  const { getIdToken } = useAuth();
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const [videoLesson, setVideoLesson] = useState<Lesson | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoMessage, setVideoMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    getIdToken()
      .then((token) => {
        if (!token) {
          throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
        }
        return fetchLessons(token, courseId);
      })
      .then((result) => {
        if (active) {
          setLessons(result);
          setFailure(null);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        setLessons(null);
        setFailure(describeApiError(error, "Não foi possível carregar as aulas."));
      });
    return () => {
      active = false;
    };
  }, [getIdToken, courseId, reloadKey]);

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

  function startEdit(lesson: Lesson) {
    setForm({
      title: lesson.title,
      description: lesson.description ?? "",
      order: String(lesson.lesson_order),
      durationMinutes: lesson.duration_seconds ? String(Math.round(lesson.duration_seconds / 60)) : "",
      materialUrl: lesson.material_url ?? "",
      status: lesson.status,
    });
    setEditingId(lesson.id);
    setFormOpen(true);
    setActionError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);

    const title = form.title.trim();
    if (!title) {
      setActionError("Informe o título da aula.");
      return;
    }

    const durationMinutes = form.durationMinutes.trim();
    const durationSeconds = durationMinutes === "" ? null : Math.round(Number(durationMinutes) * 60);
    if (
      durationSeconds !== null &&
      (Number.isNaN(durationSeconds) || durationSeconds < 0 || durationSeconds > MAX_LESSON_MINUTES * 60)
    ) {
      setActionError(`A duração deve estar entre 0 e ${MAX_LESSON_MINUTES} minutos.`);
      return;
    }

    const order = form.order.trim();
    const lessonOrder = order === "" ? null : Number(order);
    if (lessonOrder !== null && (!Number.isInteger(lessonOrder) || lessonOrder < 1)) {
      setActionError("A posição deve ser um número inteiro maior ou igual a 1.");
      return;
    }

    const base = {
      title,
      description: form.description.trim() || null,
      lesson_order: lessonOrder,
      duration_seconds: durationSeconds,
      material_url: form.materialUrl.trim() || null,
      status: form.status,
    };

    setSaving(true);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      if (editingId === null) {
        await createLesson(token, { ...base, course_id: courseId });
      } else {
        await updateLesson(token, editingId, base);
      }
      closeForm();
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível salvar a aula."));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(lesson: Lesson) {
    if (!window.confirm(`Remover a aula "${lesson.title}"?`)) {
      return;
    }
    setActionError(null);
    setBusyId(lesson.id);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      await deleteLesson(token, lesson.id);
      if (editingId === lesson.id) {
        closeForm();
      }
      if (videoLesson?.id === lesson.id) {
        setVideoLesson(null);
      }
      reload();
    } catch (error) {
      setActionError(describeApiError(error, "Não foi possível remover a aula."));
    } finally {
      setBusyId(null);
    }
  }

  function openVideo(lesson: Lesson) {
    setVideoLesson(lesson);
    setVideoFile(null);
    setUploadPercent(null);
    setVideoError(null);
    setVideoMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function handleUpload() {
    if (!videoLesson || !videoFile) {
      return;
    }
    setVideoError(null);
    setVideoMessage(null);
    setUploadPercent(0);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }
      const upload = await requestVideoUpload(token, videoLesson.id);
      await uploadVideoToCloudflare(upload.upload_url, videoFile, setUploadPercent);
      setUploadPercent(null);
      setVideoFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setVideoMessage(
        "Vídeo enviado. A Cloudflare vai processá-lo em instantes até ficar disponível para os alunos.",
      );
      reload();
    } catch (error) {
      setUploadPercent(null);
      setVideoError(describeApiError(error, "Não foi possível enviar o vídeo."));
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Aulas</h3>
          <p className="mt-1 text-sm text-slate-600">
            Máximo de {MAX_LESSON_MINUTES} minutos por aula. Cada aula pode ter um vídeo.
          </p>
        </div>
        <Button type="button" onClick={startCreate}>
          Nova aula
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
          <h4 className="text-sm font-semibold text-slate-900">
            {editingId === null ? "Nova aula" : "Editar aula"}
          </h4>
          <TextInput
            id="lesson-title"
            label="Título"
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            maxLength={200}
            required
          />
          <TextAreaField
            id="lesson-description"
            label="Descrição"
            rows={3}
            value={form.description}
            onChange={(event) =>
              setForm((current) => ({ ...current, description: event.target.value }))
            }
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextInput
              id="lesson-order"
              label="Posição (opcional)"
              type="number"
              min="1"
              value={form.order}
              onChange={(event) =>
                setForm((current) => ({ ...current, order: event.target.value }))
              }
              placeholder="Deixe vazio para usar a próxima"
            />
            <TextInput
              id="lesson-duration"
              label="Duração em minutos"
              type="number"
              min="0"
              max={MAX_LESSON_MINUTES}
              value={form.durationMinutes}
              onChange={(event) =>
                setForm((current) => ({ ...current, durationMinutes: event.target.value }))
              }
            />
          </div>
          <TextInput
            id="lesson-material"
            label="Material complementar (URL)"
            type="url"
            value={form.materialUrl}
            onChange={(event) =>
              setForm((current) => ({ ...current, materialUrl: event.target.value }))
            }
            placeholder="https://…"
          />
          <SelectField
            id="lesson-status"
            label="Situação"
            value={form.status}
            onChange={(event) =>
              setForm((current) => ({ ...current, status: event.target.value as LessonStatus }))
            }
          >
            <option value="DRAFT">Rascunho</option>
            <option value="PUBLISHED">Publicada</option>
            <option value="ARCHIVED">Arquivada</option>
          </SelectField>
          <div className="flex gap-3">
            <Button type="submit" loading={saving}>
              {editingId === null ? "Criar aula" : "Salvar alterações"}
            </Button>
            <Button type="button" variant="secondary" onClick={closeForm} disabled={saving}>
              Cancelar
            </Button>
          </div>
        </form>
      ) : null}

      <div className="mt-6">
        {failure ? (
          <Alert tone="warning" title="Não foi possível carregar as aulas">
            {failure}
          </Alert>
        ) : lessons === null ? (
          <div className="h-32 animate-pulse rounded-none bg-slate-200" aria-busy />
        ) : lessons.length === 0 ? (
          <p className="rounded-none border border-dashed border-line bg-surface p-5 text-sm text-slate-600">
            Nenhuma aula criada ainda. Adicione a primeira aula para montar o curso.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-none border border-line bg-surface">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line text-xs tracking-wide text-slate-500 uppercase">
                <tr>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    #
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Aula
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Duração
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Situação
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Vídeo
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lessons.map((lesson) => {
                  const duration = formatDuration(lesson.duration_seconds);
                  return (
                    <Fragment key={lesson.id}>
                      <tr>
                        <td className="px-4 py-3 text-slate-500">{lesson.lesson_order}</td>
                        <td className="px-4 py-3">
                          <span className="font-medium text-slate-900">{lesson.title}</span>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{duration ?? "—"}</td>
                        <td className="px-4 py-3">
                          <StatusBadge status={lesson.status} />
                        </td>
                        <td className="px-4 py-3">
                          {lesson.video_uid ? (
                            <span className="text-bone">Enviado</span>
                          ) : (
                            <span className="text-ember">Sem vídeo</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => startEdit(lesson)}
                            >
                              Editar
                            </Button>
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => openVideo(lesson)}
                            >
                              Vídeo
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              onClick={() => handleDelete(lesson)}
                              disabled={busyId === lesson.id}
                            >
                              Remover
                            </Button>
                          </div>
                        </td>
                      </tr>
                      {videoLesson?.id === lesson.id ? (
                        <tr className="bg-slate-50">
                          <td colSpan={6} className="px-4 py-4">
                            <div className="flex flex-col gap-3">
                              <p className="text-sm font-semibold text-slate-900">
                                Vídeo da aula: {lesson.title}
                              </p>
                              <input
                                ref={fileInputRef}
                                type="file"
                                accept="video/*"
                                aria-label="Arquivo de vídeo"
                                onChange={(event) =>
                                  setVideoFile(event.target.files?.[0] ?? null)
                                }
                                className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-none file:border-0 file:bg-brand-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white file:font-mono file:uppercase file:tracking-[0.18em] hover:file:bg-brand-700 hover:file:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
                              />
                              {uploadPercent !== null ? (
                                <div
                                  className="h-2 w-full overflow-hidden rounded-none bg-slate-200"
                                  role="progressbar"
                                  aria-valuenow={uploadPercent}
                                  aria-valuemin={0}
                                  aria-valuemax={100}
                                >
                                  <div
                                    className="h-full rounded-none bg-brand-600 transition-all"
                                    style={{ width: `${uploadPercent}%` }}
                                  />
                                </div>
                              ) : null}
                              {videoError ? <Alert tone="error">{videoError}</Alert> : null}
                              {videoMessage ? <Alert tone="success">{videoMessage}</Alert> : null}
                              <div className="flex gap-3">
                                <Button
                                  type="button"
                                  onClick={handleUpload}
                                  disabled={!videoFile || uploadPercent !== null}
                                >
                                  {uploadPercent !== null
                                    ? `Enviando… ${uploadPercent}%`
                                    : "Enviar vídeo"}
                                </Button>
                                <Button
                                  type="button"
                                  variant="secondary"
                                  onClick={() => setVideoLesson(null)}
                                  disabled={uploadPercent !== null}
                                >
                                  Fechar
                                </Button>
                              </div>
                              <p className="text-xs text-slate-500">
                                Use um arquivo até 200 MB. Formatos comuns (MP4, MOV, WebM) são
                                aceitos; a Cloudflare transcodifica automaticamente.
                              </p>
                            </div>
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
