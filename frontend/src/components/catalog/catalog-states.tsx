import { Alert } from "@/components/ui/alert";
import { CATALOG_UNAVAILABLE_MESSAGE } from "@/lib/catalog";

export function CatalogUnavailable() {
  return (
    <Alert tone="warning" title="Catálogo indisponível">
      {CATALOG_UNAVAILABLE_MESSAGE}
    </Alert>
  );
}

export function CatalogGridSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" aria-hidden>
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="overflow-hidden border border-line bg-surface">
          <div className="h-40 w-full animate-pulse bg-slate-100" />
          <div className="flex flex-col gap-3 p-5">
            <div className="h-3 w-20 animate-pulse rounded bg-slate-100" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-slate-100" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-slate-100" />
          </div>
        </div>
      ))}
    </div>
  );
}
