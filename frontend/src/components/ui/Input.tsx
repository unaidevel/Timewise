import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

interface FieldProps {
  label?: string;
  error?: string;
}

export function Input({
  label,
  error,
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement> & FieldProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label && <span className="font-medium text-foreground">{label}</span>}
      <input
        {...props}
        className={`rounded-md border border-input bg-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none ${className}`}
      />
      {error && <span className="text-xs text-destructive">{error}</span>}
    </label>
  );
}

export function Select({
  label,
  error,
  className = "",
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & FieldProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label && <span className="font-medium text-foreground">{label}</span>}
      <select
        {...props}
        className={`rounded-md border border-input bg-background px-3 py-2 text-foreground focus:border-ring focus:outline-none ${className}`}
      >
        {children}
      </select>
      {error && <span className="text-xs text-destructive">{error}</span>}
    </label>
  );
}

export function Textarea({
  label,
  error,
  className = "",
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & FieldProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      {label && <span className="font-medium text-foreground">{label}</span>}
      <textarea
        {...props}
        className={`rounded-md border border-input bg-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none ${className}`}
      />
      {error && <span className="text-xs text-destructive">{error}</span>}
    </label>
  );
}
