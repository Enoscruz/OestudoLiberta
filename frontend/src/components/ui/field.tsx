import type { ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

import { CONTROL_CLASS } from "./text-input";

const LABEL_CLASS =
  "font-mono text-[0.68rem] font-medium tracking-[0.18em] text-slate-500 uppercase";

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  id: string;
  label: string;
  children: ReactNode;
}

export function SelectField({ id, label, className = "", children, ...props }: SelectFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className={LABEL_CLASS}>
        {label}
      </label>
      <select {...props} id={id} className={`${CONTROL_CLASS} ${className}`}>
        {children}
      </select>
    </div>
  );
}

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  id: string;
  label: string;
  error?: string | null;
}

export function TextAreaField({
  id,
  label,
  error,
  className = "",
  ...props
}: TextAreaFieldProps) {
  const describedBy = error ? `${id}-error` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className={LABEL_CLASS}>
        {label}
      </label>
      <textarea
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
