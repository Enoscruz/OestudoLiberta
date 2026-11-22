import type { Metadata } from "next";

import { HistoryContent } from "./history-content";

export const metadata: Metadata = {
  title: "Histórico de aprendizagem",
  description: "Seus indicadores de estudo, cursos concluídos e continuidade de aprendizagem.",
};

export default function HistoryPage() {
  return <HistoryContent />;
}
