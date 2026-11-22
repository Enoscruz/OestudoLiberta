import type { Metadata } from "next";

import { CategoriesContent } from "./categories-content";

export const metadata: Metadata = {
  title: "Categorias",
  description: "Gestão das categorias que agrupam os cursos.",
};

export default function AdminCategoriesPage() {
  return <CategoriesContent />;
}
