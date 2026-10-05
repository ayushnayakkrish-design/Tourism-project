import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "@/hooks/useAuth";
import { PageLoader } from "@/components/ui/Spinner";
import { MODERATOR_ROLES, ADMIN_ROLES, type Role } from "@/api/types";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <PageLoader />
      </div>
    );
  }

  if (!user) {
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }

  return <>{children}</>;
}

export function RoleGate({
  children,
  roles,
}: {
  children: ReactNode;
  roles: Role[];
}) {
  const { user, role, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <PageLoader />
      </div>
    );
  }

  if (!user) {
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }

  if (!role || !roles.includes(role)) {
    return <Navigate to="/403" replace />;
  }

  return <>{children}</>;
}

export function ModeratorGate({ children }: { children: ReactNode }) {
  return <RoleGate roles={[...MODERATOR_ROLES]}>{children}</RoleGate>;
}

export function AdminGate({ children }: { children: ReactNode }) {
  return <RoleGate roles={[...ADMIN_ROLES]}>{children}</RoleGate>;
}
