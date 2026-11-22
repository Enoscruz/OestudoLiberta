/**
 * Selo de situação usado no painel admin para categorias, cursos e aulas.
 *
 * As cores ficam dentro da paleta: "osso" para estados vivos, vermelho de
 * sangue para rascunho/arquivado.
 */

const TONES: Record<string, string | undefined> = {
  ACTIVE: "bg-surface-2 text-bone ring-slate-300",
  PUBLISHED: "bg-surface-2 text-bone ring-slate-300",
  INACTIVE: "bg-surface text-slate-500 ring-line",
  DRAFT: "bg-brand-50 text-ember ring-brand-300",
  ARCHIVED: "bg-surface text-slate-500 ring-line",
};

const LABELS: Record<string, string | undefined> = {
  ACTIVE: "Ativa",
  INACTIVE: "Inativa",
  PUBLISHED: "Publicado",
  DRAFT: "Rascunho",
  ARCHIVED: "Arquivado",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center border px-2.5 py-0.5 font-mono text-[0.65rem] tracking-[0.14em] uppercase ${
        TONES[status] ?? "bg-surface text-slate-500 ring-line"
      }`}
    >
      {LABELS[status] ?? status}
    </span>
  );
}
