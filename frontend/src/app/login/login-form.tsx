"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/alert";
import { AuthCard } from "@/components/ui/auth-card";
import { Button } from "@/components/ui/button";
import { TextInput } from "@/components/ui/text-input";
import { useAuth } from "@/contexts/auth-context";
import { isFirebaseConfigured } from "@/lib/env";

export function LoginForm() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível entrar.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthCard
      title="Entrar"
      description="Acesse sua conta para estudar e acompanhar seu progresso."
      footer={
        <>
          Ainda não tem conta?{" "}
          <Link
            href="/cadastro"
            className="font-mono tracking-wide text-blood hover:text-blood-bright"
          >
            Criar conta
          </Link>
        </>
      }
    >
      {!isFirebaseConfigured ? (
        <Alert tone="warning" title="Firebase não configurado">
          Preencha as variáveis <code>NEXT_PUBLIC_FIREBASE_*</code> em{" "}
          <code>frontend/.env.local</code> para habilitar o login.
        </Alert>
      ) : null}

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
        <TextInput
          id="password"
          label="Senha"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <div className="flex justify-end">
          <Link
            href="/recuperar-senha"
            className="font-mono text-[0.7rem] tracking-wide text-blood hover:text-blood-bright"
          >
            Esqueci minha senha
          </Link>
        </div>
        <Button type="submit" loading={submitting}>
          Entrar
        </Button>
      </form>
    </AuthCard>
  );
}
