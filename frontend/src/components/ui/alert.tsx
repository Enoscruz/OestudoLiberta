import type { ReactNode } from "react";

type Tone = "error" | "success" | "info" | "warning";

/**
 * Tons restritos à paleta: o vermelho indica falha/atenção e o osso (bone)
 * indica sucesso/neutralidade — sem cores fora do preto + sangue.
 */
const TONES: Record<Tone, string> = {
  error: "border-blood bg-brand-50 text-ember",
  success: "border-slate-300 bg-surface-2 text-bone",
  info: "border-slate-200 bg-surface-2 text-slate-600",
  warning: "border-brand-300 bg-surface-2 text-red-800",
};

export function Alert({
  tone = "info",
  title,
  children,
}: {
  tone?: Tone;
  title?: string;
  children: ReactNode;
}) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`border-l-2 px-4 py-3 text-sm ${TONES[tone]}`}
    >
      {title ? <p className="font-display text-base tracking-wide">{title}</p> : null}
      <div className={title ? "mt-1" : undefined}>{children}</div>
    </div>
  );
}
