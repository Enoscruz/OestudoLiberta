import type { InputHTMLAttributes } from "react";

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  error?: string | null;
}

/** Estilo compartilhado dos campos de texto do site. */
export const CONTROL_CLASS =
  "rounded-none border border-slate-300 bg-void/70 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition focus:border-blood focus:ring-1 focus:ring-blood/40 focus:outline-none";

export function TextInput({ id, label, error, className = "", ...props }: TextInputProps) {
  const describedBy = error ? `${id}-error` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="font-mono text-[0.68rem] font-medium tracking-[0.18em] text-slate-500 uppercase"
      >
        {label}
      </label>
      <input
        {...props}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`${CONTROL_CLASS} ${className}`}
      />
      {error ? (
        <p id={describedBy} className="text-xs text-ember">
          {error}
        </p>
      ) : null}
    </div>
  );
}
