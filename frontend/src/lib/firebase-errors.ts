/**
 * Erros de autenticação do Firebase traduzidos para mensagens em português.
 */

const MESSAGES: Record<string, string> = {
  "auth/email-already-in-use": "Este e-mail já está cadastrado.",
  "auth/invalid-email": "E-mail inválido.",
  "auth/weak-password": "A senha é muito fraca. Use ao menos 6 caracteres.",
  "auth/user-not-found": "Não encontramos uma conta com este e-mail.",
  "auth/wrong-password": "E-mail ou senha incorretos.",
  "auth/invalid-credential": "E-mail ou senha incorretos.",
  "auth/too-many-requests": "Muitas tentativas. Aguarde alguns instantes.",
  "auth/network-request-failed": "Falha de conexão. Verifique sua internet.",
  "auth/requires-recent-login": "Faça login novamente para concluir esta ação.",
  "auth/user-disabled": "Esta conta está desativada.",
};

export function translateAuthError(error: unknown): string {
  if (typeof error === "object" && error !== null && "code" in error) {
    const code = String((error as { code: unknown }).code);
    if (code in MESSAGES) {
      return MESSAGES[code];
    }
  }
  return "Não foi possível concluir a operação. Tente novamente.";
}
