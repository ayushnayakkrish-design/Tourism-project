import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { Button } from "./Button";

interface ErrorStateProps {
  icon?: LucideIcon;
  title: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export function ErrorState({ icon: Icon, title, message, onRetry, retryLabel = "Try again", className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center py-12 px-6",
        "rounded-3xl glass-card backdrop-blur-xl",
        className
      )}
    >
      {Icon && <Icon className="w-16 h-16 text-red-400 mb-4" aria-hidden="true" />}
      <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      {message && <p className="mt-2 text-slate-600 dark:text-slate-400 max-w-sm">{message}</p>}
      {onRetry && (
        <Button variant="primary" size="md" onClick={onRetry} className="mt-6">
          {retryLabel}
        </Button>
      )}
    </div>
  );
}