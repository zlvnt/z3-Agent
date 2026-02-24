import { cn } from "@/lib/utils";

const VARIANTS: Record<string, string> = {
  social: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  direct: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  docs: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  escalate: "bg-red-500/20 text-red-300 border-red-500/30",
  error: "bg-red-500/20 text-red-300 border-red-500/30",
  default: "bg-zinc-500/20 text-zinc-300 border-zinc-500/30",
};

export function Badge({
  variant = "default",
  children,
}: {
  variant?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border",
        VARIANTS[variant] || VARIANTS.default,
      )}
    >
      {children}
    </span>
  );
}
