import { cacheLife } from "next/cache";

export async function SiteFooter() {
  "use cache";
  cacheLife("days");

  return (
    <footer className="border-t border-line bg-void">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-4 py-8 font-mono text-[0.7rem] tracking-[0.18em] text-slate-500 uppercase sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} OestudoLiberta — todos os direitos reservados</p>
        <p className="text-slate-600">
          Cursos online <span className="text-blood">{"//"}</span> pagamento por curso{" "}
          <span className="text-blood">{"//"}</span> acesso permanente
        </p>
      </div>
    </footer>
  );
}
