import { forwardRef, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg" | "xl";
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, fullWidth, disabled, children, ...props }, ref) => {
    const base = `
      inline-flex items-center justify-center gap-2 font-medium rounded-2xl
      transition-all duration-200 ease-out
      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      active:scale-[0.98]
    `;

    const variants = {
      primary: `
        bg-black text-white border-2 border-black
        hover:bg-black/90 hover:shadow-glow
        focus-visible:ring-black
      `,
      secondary: `
        bg-terracotta-600 text-white border-2 border-terracotta-600
        hover:bg-terracotta-700 hover:shadow-[0_0_25px_rgba(217,119,87,0.4)]
        focus-visible:ring-terracotta-500
      `,
      ghost: `
        bg-transparent text-slate-900 border-2 border-transparent
        hover:bg-slate-100 hover:border-slate-200
        focus-visible:ring-slate-400
        dark:text-slate-100 dark:hover:bg-slate-800 dark:hover:border-slate-700
      `,
      outline: `
        bg-transparent text-black border-2 border-black
        hover:bg-black/5
        focus-visible:ring-black
      `,
      danger: `
        bg-red-600 text-white border-2 border-red-600
        hover:bg-red-700 hover:shadow-[0_0_25px_rgba(239,68,68,0.4)]
        focus-visible:ring-red-500
      `,
    };

    const sizes = {
      sm: "px-3 py-1.5 text-sm gap-1.5",
      md: "px-5 py-2.5 text-base",
      lg: "px-7 py-3.5 text-lg gap-2",
      xl: "px-9 py-4.5 text-xl gap-2.5",
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], fullWidth && "w-full", className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";