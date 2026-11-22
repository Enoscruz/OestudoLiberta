/**
 * Formatação de valores exibidos no catálogo.
 */

const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

/** Preço vindo da API (decimal em string) no formato ``R$ 0,00``. */
export function formatPrice(value: string): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return "—";
  }
  return amount === 0 ? "Grátis" : currencyFormatter.format(amount);
}

/** Duração em segundos no formato ``12 min``. */
export function formatDuration(seconds: number | null): string | null {
  if (seconds === null || seconds <= 0) {
    return null;
  }
  const minutes = Math.max(1, Math.round(seconds / 60));
  return `${minutes} min`;
}
