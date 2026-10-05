import { Link } from "react-router-dom";
import { Compass, Home, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center py-16">
      <Compass className="w-24 h-24 mx-auto text-slate-300" aria-hidden="true" />
      <h1 className="mt-6 text-6xl font-extrabold tracking-tight">404</h1>
      <p className="mt-2 text-xl text-slate-600">This trail doesn’t exist… yet.</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link to="/">
          <Button><Home className="w-4 h-4" aria-hidden="true" /> Home</Button>
        </Link>
        <Link to="/discover">
          <Button variant="outline">Discover places</Button>
        </Link>
      </div>
    </div>
  );
}

export function ForbiddenPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center py-16">
      <ShieldAlert className="w-24 h-24 mx-auto text-amber-400" aria-hidden="true" />
      <h1 className="mt-6 text-5xl font-extrabold tracking-tight">403 — Not allowed</h1>
      <p className="mt-2 text-xl text-slate-600">
        Your role does not permit access to this area. Contact an administrator if you believe this is a mistake.
      </p>
      <div className="mt-8 flex justify-center">
        <Link to="/dashboard"><Button>Back to dashboard</Button></Link>
      </div>
    </div>
  );
}
