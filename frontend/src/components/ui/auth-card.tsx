import type { ReactNode } from "react";

export function AuthCard({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-16">
      <div className="ritual-card relative p-6 sm:p-8">
        {/* Fio de sangue no topo do cartão. */}
        <span
          aria-hidden
          className="absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-blood-bright to-transparent"
        />
        <h1 className="font-display text-2xl tracking-wide text-bone">{title}</h1>
        {description ? <p className="mt-2 text-sm text-slate-500">{description}</p> : null}
        <div className="mt-7 flex flex-col gap-4">{children}</div>
      </div>
      {footer ? (
        <div className="mt-6 text-center font-mono text-xs tracking-wider text-slate-500">
          {footer}
        </div>
      ) : null}
    </main>
  );
}
