import type { Metadata } from "next";

import { CoursesContent } from "./courses-content";

export const metadata: Metadata = {
  title: "Cursos",
  description: "Gestão do catálogo: criação, publicação e aulas.",
};

export default function AdminCoursesPage() {
  return <CoursesContent />;
}
