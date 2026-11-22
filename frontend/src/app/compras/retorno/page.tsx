import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { Alert } from "@/components/ui/alert";

export const metadata: Metadata = {
  title: "Retorno do pagamento",
  description: "Situação da compra de um curso na OestudoLiberta.",
  robots: { index: false },
};

type Tone = "success" | "warning" | "error" | "info";

interface ReturnCopy {
  tone: Tone;
  title: string;
  description: string;
}

const COPIES: Record<string, ReturnCopy> = {
  success: {
    tone: "success",
    title: "Pagamento recebido",
    description:
      "Estamos confirmando o pagamento com o Mercado Pago. O curso aparece em \"Meus cursos\" assim que a confirmação chegar.",
  },
  pending: {
    tone: "warning",
    title: "Pagamento em análise",
    description:
      "O Mercado Pago ainda está processando o pagamento. Se ele for aprovado, o acesso é liberado automaticamente.",
  },
  failure: {
    tone: "error",
    title: "Pagamento não concluído",
    description:
      "Não foi possível concluir a compra e nenhum valor foi cobrado. Você pode tentar novamente quando quiser.",
  },
};

const FALLBACK: ReturnCopy = {
  tone: "info",
  title: "Compra em andamento",
  description:
    "Acompanhe a liberação dos seus cursos na área do aluno. Se o pagamento for aprovado, o acesso aparece automaticamente.",
};

function firstParam(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default function CheckoutReturnPage({
  searchParams,
}: PageProps<"/compras/retorno">) {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-16">
      <Suspense fallback={<ReturnSkeleton />}>
        <ReturnContent searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

async function ReturnContent({ searchParams }: Pick<PageProps<"/compras/retorno">, "searchParams">) {
  const params = await searchParams;
  const status = firstParam(params.status);
  const copy = (status && COPIES[status]) || FALLBACK;

  return (
    <section className="rounded-none border border-line bg-surface p-8">
      <Alert tone={copy.tone} title={copy.title}>
        {copy.description}
      </Alert>

      <p className="mt-6 text-sm text-slate-600">
        Por segurança, o acesso nunca é liberado pelo retorno do navegador: ele depende da
        confirmação do pagamento pelo gateway.
      </p>

      <div className="mt-8 flex flex-wrap gap-4">
        <Link
          href="/dashboard"
          className="rounded-none bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white font-mono uppercase tracking-[0.18em] transition hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
        >
          Ir para meus cursos
        </Link>
        <Link
          href="/cursos"
          className="rounded-none bg-surface px-4 py-2.5 text-sm font-semibold text-slate-900 ring-1 ring-slate-300 ring-inset transition hover:bg-slate-100"
        >
          Voltar ao catálogo
        </Link>
      </div>
    </section>
  );
}

function ReturnSkeleton() {
  return (
    <div className="rounded-none border border-line bg-surface p-8" aria-hidden>
      <div className="h-4 w-40 animate-pulse rounded bg-slate-200" />
      <div className="mt-3 h-3 w-full animate-pulse rounded bg-slate-200" />
      <div className="mt-2 h-3 w-2/3 animate-pulse rounded bg-slate-200" />
    </div>
  );
}
