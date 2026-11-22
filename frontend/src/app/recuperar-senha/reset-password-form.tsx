"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/alert";
import { AuthCard } from "@/components/ui/auth-card";
import { Button } from "@/components/ui/button";
import { TextInput } from "@/components/ui/text-input";
import { useAuth } from "@/contexts/auth-context";
import { isFirebaseConfigured } from "@/lib/env";

export function ResetPasswordForm() {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await resetPassword(email);
      setSent(true);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Não foi possível enviar o e-mail de recuperação.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthCard
      title="Recuperar senha"
      description="Informe seu e-mail e enviaremos um link para redefinir a senha."
      footer={
        <>
          Lembrou a senha?{" "}
          <Link href="/login" className="font-mono tracking-wide text-blood hover:text-blood-bright">
            Voltar para o login
          </Link>
        </>
      }
    >
      {!isFirebaseConfigured ? (
        <Alert tone="warning" title="Firebase não configurado">
          Preencha as variáveis <code>NEXT_PUBLIC_FIREBASE_*</code> em{" "}
          <code>frontend/.env.local</code> para habilitar a recuperação de senha.
        </Alert>
      ) : null}

      {sent ? (
        <Alert tone="success" title="E-mail enviado">
          Se houver uma conta com <strong>{email}</strong>, você receberá um link para redefinir a
          senha. Verifique também a caixa de spam.
        </Alert>
      ) : (
        <>
          {error ? <Alert tone="error">{error}</Alert> : null}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <TextInput
              id="email"
              label="E-mail"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <Button type="submit" loading={submitting}>
              Enviar link de recuperação
            </Button>
          </form>
        </>
      )}
    </AuthCard>
  );
}
