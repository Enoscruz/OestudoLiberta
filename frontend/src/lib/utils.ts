/**
 * Utilitários de classes CSS.
 *
 * `cn` concatena classes descartando valores vazios/nulos. Mantido sem
 * dependências externas de propósito: o projeto só precisa do caso simples de
 * composição condicional (ver `words-stagger.tsx`).
 */

export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
