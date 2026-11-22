import { redirect } from "next/navigation";

/** A porta de entrada do painel é a gestão de cursos. */
export default function AdminIndexPage() {
  redirect("/admin/cursos");
}
