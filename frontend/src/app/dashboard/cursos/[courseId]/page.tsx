import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PlayerContent } from "./player-content";

// A página depende inteiramente do `courseId`; bloquear a navegação mantém o
// status HTTP correto (404) em vez de um shell estático com soft-404.
export const instant = false;

export const metadata: Metadata = {
  title: "Aula",
};

export default async function PlayerPage({ params }: PageProps<"/dashboard/cursos/[courseId]">) {
  const { courseId } = await params;

  // Um id não numérico nunca corresponde a um curso: evita exibir uma mensagem
  // de erro para uma URL inválida.
  if (!/^\d+$/.test(courseId)) {
    notFound();
  }

  return <PlayerContent courseId={courseId} />;
}
