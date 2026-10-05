import { HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface GlassPanelProps extends HTMLAttributes<HTMLDivElement> {
  intensity?: "light" | "medium" | "dark" | "card";
  blur?: "xs" | "md" | "xl" | "2xl";
}

export const GlassPanel = forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, intensity = "card", blur = "xl", children, ...props }, ref) => {
    const intensities = {
      light: "bg-white/75 border-white/35 dark:bg-slate-900/75 dark:border-white/15",
      medium: "bg-white/55 border-white/35 dark:bg-slate-900/55 dark:border-white/15",
      dark: "bg-slate-950/75 border-white/15",
      card: "bg-white/85 dark:bg-slate-900/85 border-white/35 dark:border-white/15",
    };

    const blurs = {
      xs: "backdrop-blur-xs",
      md: "backdrop-blur-md",
      xl: "backdrop-blur-xl",
      "2xl": "backdrop-blur-2xl",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "rounded-3xl border-2 transition-all duration-300",
          intensities[intensity],
          blurs[blur],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GlassPanel.displayName = "GlassPanel";