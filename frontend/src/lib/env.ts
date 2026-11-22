/**
 * Configuração de ambiente do frontend.
 *
 * Next.js só expõe ao navegador variáveis com o prefixo `NEXT_PUBLIC_`.
 * Nenhuma credencial secreta (chave de conta de serviço, tokens) pode viver aqui.
 */

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN ?? "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID ?? "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ?? "",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET ?? "",
};

/**
 * Indica se as credenciais Web do Firebase foram informadas.
 *
 * Enquanto forem placeholders vazios, as telas de autenticação exibem um aviso
 * em vez de falhar silenciosamente.
 */
export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId,
);
