import type { Metadata } from "next";

import { VerifyEmailContent } from "./verify-email-content";

export const metadata: Metadata = {
  title: "Confirmar e-mail",
};

export default function VerifyEmailPage() {
  return <VerifyEmailContent />;
}
