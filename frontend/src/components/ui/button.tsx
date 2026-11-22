import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)] focus-visible:outline-brand-600 disabled:bg-brand-300",
  secondary:
    "bg-surface-2 text-slate-800 ring-1 ring-slate-300 ring-inset hover:bg-slate-100 hover:ring-blood focus-visible:outline-slate-500",
  ghost: "text-slate-600 hover:bg-brand-50 hover:text-blood-bright focus-visible:outline-slate-500",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-none px-4 py-2.5 font-mono text-[0.72rem] font-semibold tracking-[0.18em] uppercase transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
    >
      {loading ? "Aguarde..." : children}
    </button>
  );
}
