"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/contexts/auth-context";

const NAV_LINK =
  "text-[0.7rem] font-mono tracking-[0.18em] uppercase text-slate-500 transition hover:text-blood-bright";

export function SiteHeader() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    await logout();
    setMenuOpen(false);
    router.push("/");
  }

  const mobileLink = "rounded-none px-3 py-2 hover:bg-brand-50 hover:text-blood-bright";

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-void/85 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link
          href="/"
          className="font-display text-base font-bold tracking-[0.22em] text-bone uppercase"
        >
          Oestudo<span className="text-blood-bright text-glow">Liberta</span>
        </Link>

        <nav className="hidden items-center gap-7 md:flex">
          <Link href="/" className={NAV_LINK}>
            Início
          </Link>
          <Link href="/cursos" className={NAV_LINK}>
            Cursos
          </Link>
          <Link href="/dashboard" className={NAV_LINK}>
            Meus cursos
          </Link>
          <Link href="/dashboard/historico" className={NAV_LINK}>
            Histórico
          </Link>
          {user?.role.name === "ADMIN" ? (
            <Link href="/admin" className={NAV_LINK}>
              Painel admin
            </Link>
          ) : null}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {loading ? null : user ? (
            <>
              <span className="font-mono text-xs tracking-wider text-slate-500">{user.name}</span>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-none border border-line px-3 py-2 font-mono text-[0.7rem] tracking-[0.18em] text-slate-600 uppercase transition hover:border-blood hover:text-blood-bright"
              >
                Sair
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="px-3 py-2 font-mono text-[0.7rem] tracking-[0.18em] text-slate-600 uppercase transition hover:text-blood-bright"
              >
                Entrar
              </Link>
              <Link
                href="/cadastro"
                className="bg-brand-600 px-4 py-2 font-mono text-[0.7rem] tracking-[0.18em] text-white uppercase transition hover:bg-brand-700 hover:shadow-[0_0_26px_-6px_var(--color-blood-bright)]"
              >
                Criar conta
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          aria-expanded={menuOpen}
          aria-label="Abrir menu"
          onClick={() => setMenuOpen((open) => !open)}
          className="p-2 text-slate-600 transition hover:text-blood-bright md:hidden"
        >
          <span className="block h-0.5 w-5 bg-current" />
          <span className="mt-1 block h-0.5 w-5 bg-current" />
          <span className="mt-1 block h-0.5 w-5 bg-current" />
        </button>
      </div>

      {menuOpen ? (
        <div className="border-t border-line bg-surface px-4 py-3 md:hidden">
          <nav className="flex flex-col gap-1 font-mono text-xs tracking-[0.18em] text-slate-500 uppercase">
            <Link href="/" onClick={() => setMenuOpen(false)} className={mobileLink}>
              Início
            </Link>
            <Link href="/cursos" onClick={() => setMenuOpen(false)} className={mobileLink}>
              Cursos
            </Link>
            <Link href="/dashboard" onClick={() => setMenuOpen(false)} className={mobileLink}>
              Meus cursos
            </Link>
            <Link
              href="/dashboard/historico"
              onClick={() => setMenuOpen(false)}
              className={mobileLink}
            >
              Histórico
            </Link>
            {user?.role.name === "ADMIN" ? (
              <Link href="/admin" onClick={() => setMenuOpen(false)} className={mobileLink}>
                Painel admin
              </Link>
            ) : null}
            <div className="mt-2 border-t border-line pt-2">
              {loading ? null : user ? (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full px-3 py-2 text-left hover:bg-brand-50 hover:text-blood-bright"
                >
                  Sair ({user.name})
                </button>
              ) : (
                <div className="flex gap-2">
                  <Link
                    href="/login"
                    onClick={() => setMenuOpen(false)}
                    className="flex-1 px-3 py-2 text-center hover:bg-brand-50 hover:text-blood-bright"
                  >
                    Entrar
                  </Link>
                  <Link
                    href="/cadastro"
                    onClick={() => setMenuOpen(false)}
                    className="flex-1 bg-brand-600 px-3 py-2 text-center font-semibold text-white hover:bg-brand-700"
                  >
                    Criar conta
                  </Link>
                </div>
              )}
            </div>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
