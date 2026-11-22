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

export function RegisterForm() {
  const { register, user, loading } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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

    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }

    setSubmitting(true);
    try {
      await register(name, email, password);
      router.push("/verificar-email");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível criar a conta.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthCard
      title="Criar conta"
      description="Cadastre-se para acompanhar seus cursos e seu progresso."
      footer={
        <>
          Já tem uma conta?{" "}
          <Link href="/login" className="font-mono tracking-wide text-blood hover:text-blood-bright">
            Entrar
          </Link>
        </>
      }
    >
      {!isFirebaseConfigured ? (
        <Alert tone="warning" title="Firebase não configurado">
          Preencha as variáveis <code>NEXT_PUBLIC_FIREBASE_*</code> em{" "}
          <code>frontend/.env.local</code> para habilitar o cadastro.
        </Alert>
      ) : null}

      {error ? <Alert tone="error">{error}</Alert> : null}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <TextInput
          id="name"
          label="Nome completo"
          type="text"
          autoComplete="name"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
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
          autoComplete="new-password"
          minLength={6}
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <TextInput
          id="confirm-password"
          label="Confirmar senha"
          type="password"
          autoComplete="new-password"
          minLength={6}
          required
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />
        <Button type="submit" loading={submitting}>
          Criar conta
        </Button>
      </form>
    </AuthCard>
  );
}
