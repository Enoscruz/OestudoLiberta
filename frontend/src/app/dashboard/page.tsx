import type { Metadata } from "next";

import { DashboardContent } from "./dashboard-content";

export const metadata: Metadata = {
  title: "Meus cursos",
  description: "Cursos liberados para o seu acesso na OestudoLiberta.",
};

export default function DashboardPage() {
  return <DashboardContent />;
}
