"use client";

/**
 * Moldura da área administrativa.
 *
 * Protege todas as rotas `/admin/*` no cliente (`useRequireAuth`) e oferece a
 * navegação entre as seções. É uma conveniência de interface: cada chamada à
 * API é revalidada como ADMIN pelo backend.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useRequireAuth } from "@/hooks/use-require-auth";

const NAV_ITEMS = [
  { href: "/admin/cursos", label: "Cursos" },
  { href: "/admin/categorias", label: "Categorias" },
];

export function AdminShell({ children }: { children: ReactNode }) {
  const { ready } = useRequireAuth({ adminOnly: true });
  const pathname = usePathname();

  if (!ready) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 py-12" aria-busy>
        <div className="h-8 w-56 animate-pulse bg-slate-100" />
        <div className="mt-8 h-64 animate-pulse bg-slate-100" />
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-10">
      <header className="border-b border-line pb-6">
        <p className="eyebrow text-blood">Administração</p>
        <h1 className="mt-2 font-display text-3xl tracking-wide text-bone">Painel admin</h1>
      </header>

      <div className="mt-6 grid gap-8 lg:grid-cols-[14rem_minmax(0,1fr)]">
        <nav aria-label="Seções administrativas" className="flex flex-wrap gap-2 lg:flex-col">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`border-l-2 px-3 py-2 font-mono text-[0.7rem] tracking-[0.18em] uppercase transition ${
                  active
                    ? "border-blood-bright bg-brand-50 text-blood-bright"
                    : "border-transparent text-slate-500 hover:border-blood hover:text-slate-800"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="min-w-0">{children}</div>
      </div>
    </main>
  );
}
