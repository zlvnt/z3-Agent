import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  sub,
  color = "text-white",
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <Card>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <p className={cn("text-2xl font-bold", color)}>{value}</p>
      {sub && <p className="text-xs text-zinc-500 mt-1">{sub}</p>}
    </Card>
  );
}
