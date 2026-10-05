import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export function RegisterPage() {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!email.includes("@")) next.email = "Enter a valid email address.";
    if (displayName.trim().length < 1) next.displayName = "Enter a display name.";
    if (password.length < 10) next.password = "Password must be at least 10 characters.";
    if (confirm !== password) next.confirm = "Passwords do not match.";
    setErrors(next);
    if (Object.keys(next).length) return;

    setLoading(true);
    try {
      await register({ email: email.trim(), password, display_name: displayName.trim() });
      showToast({ type: "success", title: "Account created!", message: "Welcome to Wandor." });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      showToast({ type: "error", title: "Registration failed", message: errorMessage(err) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 sm:px-6">
      <div className="rounded-[2.5rem] overflow-hidden relative">
        <img
          src="https://images.unsplash.com/photo-1503220317375-aaad61436b1b?auto=format&fit=crop&w=1200&q=80"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-black/10" />
        <div className="relative p-8 pt-14 text-white">
          <p className="font-wandor text-xl opacity-90">Wandor</p>
          <h1 className="text-3xl font-extrabold mt-1">Start your journey</h1>
          <p className="text-white/80 mt-1">Free forever. Earn rewards as you travel.</p>
        </div>
      </div>

      <Card variant="glass" className="-mt-8 relative z-10 mx-2">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5" aria-hidden="true" /> Create account
          </CardTitle>
          <CardDescription>POST /api/auth/register · instant Bearer session</CardDescription>
          <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
            <Input
              label="Display name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Alex Explorer"
              error={errors.displayName}
              autoComplete="nickname"
            />
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
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 10 characters"
              error={errors.password}
              helperText="Minimum 10 characters per backend policy."
            />
            <Input
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repeat your password"
              error={errors.confirm}
            />
            <Button type="submit" loading={loading} fullWidth size="lg">
              Plan My Trip
            </Button>
          </form>
          <p className="mt-5 text-sm text-center text-slate-600">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-terracotta-700 hover:underline">
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
