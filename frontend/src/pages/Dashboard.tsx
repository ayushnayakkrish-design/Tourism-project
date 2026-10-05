import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  MapPin, Route, Sparkles, Plane, Wallet, Gift, Users,
  ArrowRight, Coins, TrendingUp, CheckCircle2,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { walletApi, rewardsApi } from "@/api/rewards";
import { visitsApi } from "@/api/visits";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatPoints, formatDate } from "@/lib/utils";

const QUICK_ACTIONS = [
  { to: "/discover", icon: MapPin, title: "Discover places", desc: "Search & explore real destinations", cta: "Search" },
  { to: "/itinerary", icon: Sparkles, title: "Plan a trip", desc: "AI multi-day itineraries", cta: "Generate" },
  { to: "/routes", icon: Route, title: "Routes & traffic", desc: "Directions & travel matrix", cta: "Route" },
  { to: "/visits", icon: Plane, title: "Check in", desc: "Verify visits, earn points", cta: "Visit" },
  { to: "/rewards", icon: Gift, title: "Rewards", desc: "Redeem catalog rewards", cta: "Browse" },
  { to: "/community", icon: Users, title: "Community", desc: "Submit places & reviews", cta: "Share" },
];

export function Dashboard() {
  const { user, role } = useAuth();

  const walletQ = useQuery({ queryKey: ["wallet"], queryFn: () => walletApi.get() });
  const visitsQ = useQuery({
    queryKey: ["visits", "recent"],
    queryFn: () => visitsApi.list({ page: 1, page_size: 5 }),
  });
  const rewardsQ = useQuery({
    queryKey: ["rewards", "catalog-preview"],
    queryFn: () => rewardsApi.list({ available_only: true }),
  });

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-8">
      {/* Welcome hero */}
      <section className="relative overflow-hidden rounded-[2.5rem] bg-black text-white">
        <img
          src="https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1800&q=80"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover opacity-50"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/30 to-transparent" />
        <div className="relative px-8 py-12 sm:px-12">
          <p className="font-wandor text-lg text-white/80">Namaste,</p>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            {user?.display_name || "Traveler"}
          </h1>
          <p className="mt-2 text-white/75 max-w-lg">
            Your travel operating system is ready — balance, visits and rewards at a glance.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            {walletQ.data ? (
              <div className="flex items-center gap-3 rounded-2xl border-2 border-white/30 bg-white/15 backdrop-blur-xl px-5 py-3">
                <Coins className="w-6 h-6 text-amber-300" aria-hidden="true" />
                <div>
                  <p className="text-2xl font-extrabold">{formatPoints(walletQ.data.balance)} pts</p>
                  <p className="text-xs text-white/70">GET /api/wallet · role {role}</p>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border-2 border-white/30 bg-white/15 px-5 py-3 text-sm">
                Loading wallet…
              </div>
            )}
            <Link
              to="/itinerary"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-white text-black font-semibold hover:bg-white/90 active:scale-95 transition"
            >
              <Sparkles className="w-5 h-5" aria-hidden="true" /> Plan My Trip
            </Link>
          </div>
        </div>
      </section>

      {/* Quick actions */}
      <section aria-label="Quick actions">
        <h2 className="text-2xl font-extrabold tracking-tight">What will you do today?</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger">
          {QUICK_ACTIONS.map(({ to, icon: Icon, title, desc, cta }) => (
            <Link key={to} to={to}>
              <Card variant="glass" interactive className="h-full">
                <CardContent className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-black text-white flex items-center justify-center shrink-0">
                    <Icon className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold">{title}</h3>
                    <p className="text-sm text-slate-600">{desc}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-terracotta-700">
                    {cta} <ArrowRight className="w-4 h-4" aria-hidden="true" />
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Recent activity */}
      <section className="grid gap-6 lg:grid-cols-2" aria-label="Recent activity">
        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-extrabold tracking-tight">Recent visits</h2>
            <Link to="/visits" className="text-sm font-semibold text-terracotta-700 hover:underline">
              View all
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {visitsQ.isLoading && <SkeletonCard />}
            {visitsQ.data && visitsQ.data.items.length === 0 && (
              <EmptyState
                icon={Plane}
                title="No visits yet"
                description="Check in at a place to earn your first points."
                action={<Link to="/visits"><Button size="sm">Check in now</Button></Link>}
              />
            )}
            {visitsQ.data?.items.map((v) => (
              <Card key={v.id} variant="glass">
                <CardContent className="flex items-center gap-3 py-4">
                  <div className="w-10 h-10 rounded-xl bg-terracotta-100 text-terracotta-700 flex items-center justify-center shrink-0">
                    <MapPin className="w-5 h-5" aria-hidden="true" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{v.place_id}</p>
                    <p className="text-xs text-slate-500">{formatDate(v.timestamp)}</p>
                  </div>
                  <Badge variant={v.status === "VERIFIED" ? "success" : v.status === "FLAGGED" ? "warning" : "danger"}>
                    {v.status}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-extrabold tracking-tight">Reward highlights</h2>
            <Link to="/rewards" className="text-sm font-semibold text-terracotta-700 hover:underline">
              View catalog
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {rewardsQ.isLoading && <SkeletonCard />}
            {rewardsQ.data?.items.slice(0, 3).map((r) => (
              <Card key={r.id} variant="glass">
                <CardContent className="flex items-center gap-3 py-4">
                  <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                    <Gift className="w-5 h-5" aria-hidden="true" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{r.name}</p>
                    <p className="text-xs text-slate-500 flex items-center gap-1">
                      <Coins className="w-3 h-3" aria-hidden="true" /> {formatPoints(r.points_required)} pts
                      {r.stock != null && <> · {r.stock} left</>}
                    </p>
                  </div>
                  <Link to="/rewards">
                    <Button size="sm" variant="outline">Redeem</Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card variant="glass" className="mt-4">
            <CardContent>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="w-5 h-5 text-emerald-600" aria-hidden="true" />
                How earning works
              </CardTitle>
              <CardDescription>
                Every verified visit grants points; photo proof grants a bonus. Points land in your
                wallet with a ledger entry you can audit anytime.
              </CardDescription>
              <div className="mt-3 flex items-center gap-2 text-sm text-emerald-700 font-medium">
                <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
                Backend-authoritative balances — the UI never invents points.
              </div>
              <div className="mt-4 flex gap-2">
                <Link to="/wallet"><Button size="sm" variant="secondary"><Wallet className="w-4 h-4" aria-hidden="true" /> Wallet</Button></Link>
                <Link to="/crowd"><Button size="sm" variant="ghost">Crowd intel</Button></Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
