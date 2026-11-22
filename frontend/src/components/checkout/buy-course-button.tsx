"use client";

/**
 * Botão de compra do curso, exibido na página pública do catálogo.
 *
 * Inicia a compra no backend e envia o aluno ao checkout do Mercado Pago.
 * Nada aqui libera acesso: a matrícula é criada pelo webhook confirmado do
 * gateway, nunca pelo retorno do navegador.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api";
import { createCheckout } from "@/services/purchase-service";

interface BuyCourseButtonProps {
  courseId: number;
  /** Curso sem custo: o acesso é liberado na hora, sem passar pelo checkout. */
  free?: boolean;
}

interface BuyFailure {
  message: string;
  /** O backend recusou o acesso porque o e-mail não está confirmado. */
  needsVerification: boolean;
}

export function BuyCourseButton({ courseId, free = false }: BuyCourseButtonProps) {
  const { user, loading, getIdToken } = useAuth();
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [failure, setFailure] = useState<BuyFailure | null>(null);
  const [alreadyOwned, setAlreadyOwned] = useState(false);

  const handleBuy = async () => {
    setFailure(null);
    setSubmitting(true);
    try {
      const token = await getIdToken();
      if (!token) {
        throw new ApiError(401, "Sua sessão expirou. Entre novamente.");
      }

      const session = await createCheckout(token, courseId);
      if (session.requires_payment && session.init_point) {
        // Sai da aplicação: o gateway assume o fluxo de pagamento.
        window.location.assign(session.init_point);
        return;
      }

      // Curso gratuito: o backend já liberou o acesso.
      router.push(`/dashboard/cursos/${courseId}`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setAlreadyOwned(true);
        return;
      }
      setFailure(
        error instanceof ApiError
          ? { message: error.message, needsVerification: error.status === 403 }
          : {
              message: "Não foi possível iniciar a compra agora. Tente novamente.",
              needsVerification: false,
            },
      );
      setSubmitting(false);
    }
  };

  if (alreadyOwned) {
    return (
      <div className="flex flex-col gap-3 sm:items-end">
        <Alert tone="info" title="Você já tem acesso a este curso">
          Continue de onde parou na sua área do aluno.
        </Alert>
        <Link
          href={`/dashboard/cursos/${courseId}`}
          className="text-sm font-semibold text-brand-600 hover:text-blood-bright"
        >
          Ir para o curso →
        </Link>
      </div>
    );
  }

  if (loading) {
    return <Button loading>Verificando sessão...</Button>;
  }

  if (!user) {
    return (
      <div className="flex flex-col gap-2 sm:items-end">
        <Link
          href="/login"
          className="inline-flex items-center justify-center rounded-none bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white font-mono uppercase tracking-[0.18em] transition hover:bg-brand-700 hover:shadow-[0_0_28px_-8px_var(--color-blood-bright)]"
        >
          Entrar para comprar
        </Link>
        <p className="text-xs text-slate-500">É preciso uma conta para adquirir o curso.</p>
      </div>
    );
  }

  return (
    <div className="flex w-full flex-col gap-3 sm:w-auto sm:items-end">
      <Button type="button" onClick={handleBuy} loading={submitting} className="w-full sm:w-auto">
        {free ? "Matricular-se gratuitamente" : "Comprar curso"}
      </Button>

      {failure ? (
        <div className="flex w-full flex-col gap-2 sm:max-w-xs">
          <Alert tone="error">{failure.message}</Alert>
          {failure.needsVerification ? (
            <Link
              href="/verificar-email"
              className="self-start text-sm font-semibold text-brand-600 hover:text-blood-bright"
            >
              Confirmar e-mail →
            </Link>
          ) : null}
        </div>
      ) : (
        <p className="text-xs text-slate-500 sm:text-right">
          A liberação do acesso acontece após a confirmação do pagamento.
        </p>
      )}
    </div>
  );
}
