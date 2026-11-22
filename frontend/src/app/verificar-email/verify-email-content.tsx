"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { AuthCard } from "@/components/ui/auth-card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";

export function VerifyEmailContent() {
  const { user, loading, refresh, resendVerificationEmail } = useAuth();
  const router = useRouter();
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resending, setResending] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  async function handleResend() {
    setError(null);
    setFeedback(null);
    setResending(true);
    try {
      await resendVerificationEmail();
      setFeedback("E-mail de confirmação reenviado. Verifique sua caixa de entrada.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível reenviar o e-mail.");
    } finally {
      setResending(false);
    }
  }

  async function handleCheck() {
    setError(null);
    setFeedback(null);
    setChecking(true);
    try {
      await refresh();
      setFeedback(
        "Status atualizado. Se o e-mail já foi confirmado, você será direcionado ao painel.",
      );
    } catch {
      setError("Não foi possível verificar o status. Tente novamente.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <AuthCard
      title="Confirme seu e-mail"
      description="Enviamos um link de confirmação para o seu e-mail. Confirme para liberar o acesso completo."
      footer={
        <Link
          href="/dashboard"
          className="font-mono tracking-wide text-blood hover:text-blood-bright"
        >
          Ir para o painel
        </Link>
      }
    >
      {feedback ? <Alert tone="success">{feedback}</Alert> : null}
      {error ? <Alert tone="error">{error}</Alert> : null}

      <div className="flex flex-col gap-3">
        <Button type="button" onClick={handleResend} loading={resending}>
          Reenviar e-mail de confirmação
        </Button>
        <Button type="button" variant="secondary" onClick={handleCheck} loading={checking}>
          Já confirmei, verificar agora
        </Button>
      </div>
    </AuthCard>
  );
}
