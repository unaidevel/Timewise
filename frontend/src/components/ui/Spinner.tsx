export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900 ${className}`}
      role="status"
      aria-label="Cargando"
    />
  );
}

export function FullPageSpinner() {
  return (
    <div className="flex h-full items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  );
}
