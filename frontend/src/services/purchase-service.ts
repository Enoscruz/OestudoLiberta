/**
 * Chamadas de compra do aluno ao backend.
 *
 * O frontend apenas inicia a compra: a liberação do acesso é decidida pelo
 * backend, quando o webhook do Mercado Pago confirma o pagamento.
 */

import { apiFetch } from "@/lib/api";
import type { CheckoutSession } from "@/types/api";

/** Inicia a compra de um curso e devolve o endereço de checkout do gateway. */
export function createCheckout(token: string, courseId: number): Promise<CheckoutSession> {
  return apiFetch<CheckoutSession>("/purchases", {
    method: "POST",
    token,
    body: { course_id: courseId },
  });
}
