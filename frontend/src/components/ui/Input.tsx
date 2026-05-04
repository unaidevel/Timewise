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
      {label && <span className="font-medium text-slate-700">{label}</span>}
      <input
        {...props}
        className={`rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-slate-900 focus:outline-none ${className}`}
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
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
      {label && <span className="font-medium text-slate-700">{label}</span>}
      <select
        {...props}
        className={`rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:border-slate-900 focus:outline-none ${className}`}
      >
        {children}
      </select>
      {error && <span className="text-xs text-red-600">{error}</span>}
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
      {label && <span className="font-medium text-slate-700">{label}</span>}
      <textarea
        {...props}
        className={`rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-slate-900 focus:outline-none ${className}`}
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
    </label>
  );
}
