import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { LogIn } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export function LoginPage() {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: typeof errors = {};
    if (!email.includes("@")) next.email = "Enter a valid email address.";
    if (password.length < 1) next.password = "Enter your password.";
    setErrors(next);
    if (Object.keys(next).length) return;

    setLoading(true);
    try {
      await login(email.trim(), password);
      showToast({ type: "success", title: "Welcome back!", message: "You are signed in." });
      const redirect = params.get("redirect");
      navigate(redirect && redirect.startsWith("/") ? redirect : "/dashboard", { replace: true });
    } catch (err) {
      showToast({ type: "error", title: "Login failed", message: errorMessage(err) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 sm:px-6">
      <div className="rounded-[2.5rem] overflow-hidden relative">
        <img
          src="https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-black/10" />
        <div className="relative p-8 pt-14 text-white">
          <p className="font-wandor text-xl opacity-90">Wandor</p>
          <h1 className="text-3xl font-extrabold mt-1">Welcome back, traveler</h1>
          <p className="text-white/80 mt-1">Sign in to continue your journey.</p>
        </div>
      </div>

      <Card variant="glass" className="-mt-8 relative z-10 mx-2">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <LogIn className="w-5 h-5" aria-hidden="true" /> Log in
          </CardTitle>
          <CardDescription>POST /api/auth/login · Bearer session</CardDescription>
          <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              error={errors.email}
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              error={errors.password}
            />
            <Button type="submit" loading={loading} fullWidth size="lg">
              Log in
            </Button>
          </form>
          <p className="mt-5 text-sm text-center text-slate-600">
            New to Wandor?{" "}
            <Link to="/register" className="font-semibold text-terracotta-700 hover:underline">
              Create an account
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
