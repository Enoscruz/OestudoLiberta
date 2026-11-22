/**
 * Inicialização do Firebase Web SDK (uso exclusivo no cliente).
 *
 * A inicialização é preguiçosa: se as credenciais ainda não foram configuradas,
 * `getFirebaseAuth()` devolve `null` e a interface mostra um aviso, em vez de
 * quebrar a aplicação.
 */

import { getApps, initializeApp, type FirebaseApp } from "firebase/app";
import { getAuth, type Auth } from "firebase/auth";

import { firebaseConfig, isFirebaseConfigured } from "./env";

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

export function getFirebaseAuth(): Auth | null {
  if (!isFirebaseConfigured) {
    return null;
  }
  if (!app) {
    app = getApps()[0] ?? initializeApp(firebaseConfig);
  }
  if (!auth) {
    auth = getAuth(app);
  }
  return auth;
}
