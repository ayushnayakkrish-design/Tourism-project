import { createContext, useContext, useState, ReactNode, useCallback } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, "id">) => string;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(({ duration = 5000, ...rest }: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).slice(2, 10);
    setToasts((t) => [...t, { id, ...rest, duration }]);
    return id;
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  return (
    <div
      className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none"
      role="region"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const typeStyles: Record<ToastType, string> = {
    success: "border-emerald-500/50 bg-emerald-50/90 text-emerald-900",
    error: "border-red-500/50 bg-red-50/90 text-red-900",
    warning: "border-amber-500/50 bg-amber-50/90 text-amber-900",
    info: "border-sky-500/50 bg-sky-50/90 text-sky-900",
  };

  const icons: Record<ToastType, string> = {
    success: "check-circle",
    error: "alert-circle",
    warning: "alert-triangle",
    info: "info",
  };

  return (
    <div
      className={`
        pointer-events-auto min-w-[300px] max-w-md rounded-2xl border-2 p-4 shadow-xl
        glass-card backdrop-blur-xl
        animate-in slide-in-from-right-4 duration-300 ease-out
        ${typeStyles[toast.type]}
      `}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <i className={`lucide lucide-${icons[toast.type]} w-5 h-5`} aria-hidden="true" />
        </div>
        <div className="flex-1 min-w-0">
          {toast.title && <p className="font-medium text-sm">{toast.title}</p>}
          {toast.message && <p className="text-sm opacity-80 mt-0.5">{toast.message}</p>}
        </div>
        <button
          onClick={() => onDismiss(toast.id)}
          className="flex-shrink-0 opacity-50 hover:opacity-100 transition p-1"
          aria-label="Dismiss"
        >
          <i className="lucide lucide-x w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}