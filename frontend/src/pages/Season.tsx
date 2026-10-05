import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sun, CloudRain, Users, Accessibility, Trophy, Calendar } from "lucide-react";
import { seasonApi } from "@/api/crowd";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { Badge } from "@/components/ui/Badge";
import { scoreColor, scoreBarColor } from "@/lib/utils";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function SeasonPage() {
  const { placeId } = useParams<{ placeId?: string }>();
  const target = placeId || "demo_konark";

  const seasonQ = useQuery({
    queryKey: ["season", target],
    queryFn: () => seasonApi.getForPlace(target),
  });

  const profiles = seasonQ.data?.profiles || [];
  const bestMonth = seasonQ.data?.best_month;

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Seasonal intelligence</h1>
        <p className="mt-1 text-slate-600">GET /api/season/{target} · transparent weighted scores</p>
      </header>

      {seasonQ.isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {bestMonth && (
        <Card variant="glass" className="overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-br from-terracotta-600/90 to-amber-600/90" aria-hidden="true" />
          <CardContent className="relative z-10 text-white">
            <p className="flex items-center gap-2 text-sm font-semibold">
              <Trophy className="w-4 h-4" aria-hidden="true" /> Best month to visit
            </p>
            <h2 className="text-4xl font-extrabold mt-1">{MONTHS[bestMonth.month - 1]}</h2>
            <p className="mt-2 text-white/90">
              Overall score {bestMonth.overall_score}/100
            </p>
            <p className="text-sm text-white/80 mt-1 max-w-xl">
              {bestMonth.reason || "Calculated from weather, crowd, festival and accessibility factors."}
            </p>
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { icon: Sun, label: "Weather", value: bestMonth.weather_score },
                { icon: Users, label: "Crowd", value: bestMonth.crowd_score },
                { icon: CloudRain, label: "Festival", value: bestMonth.festival_score },
                { icon: Accessibility, label: "Access", value: bestMonth.accessibility_score },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} className="rounded-2xl bg-white/20 backdrop-blur px-4 py-3">
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  <p className="text-2xl font-extrabold mt-1">{value}</p>
                  <p className="text-xs opacity-80">{label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger">
        {profiles.map((p) => (
          <Card key={p.month} variant="glass" interactive>
            <CardContent>
              <div className="flex items-center justify-between">
                <p className="flex items-center gap-2 font-bold text-lg">
                  <Calendar className="w-4 h-4 text-terracotta-600" aria-hidden="true" />
                  {MONTHS[p.month - 1]}
                </p>
                <span className={`text-2xl font-extrabold ${scoreColor(p.overall_score)}`}>
                  {p.overall_score}
                </span>
              </div>
              <div className="mt-3 space-y-2">
                {[
                  { icon: Sun, label: "Weather", value: p.weather_score },
                  { icon: Users, label: "Crowd", value: p.crowd_score },
                  { icon: CloudRain, label: "Festival", value: p.festival_score },
                  { icon: Accessibility, label: "Access", value: p.accessibility_score },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="flex items-center gap-2 text-sm">
                    <Icon className="w-4 h-4 text-slate-400" aria-hidden="true" />
                    <span className="w-20 text-slate-600">{label}</span>
                    <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div className={`h-full rounded-full ${scoreBarColor(value)}`} style={{ width: `${value}%` }} aria-hidden="true" />
                    </div>
                    <span className="font-semibold w-8 text-right">{value}</span>
                  </div>
                ))}
              </div>
              {p.reason && <p className="mt-3 text-xs text-slate-500">{p.reason}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      {!seasonQ.isLoading && profiles.length === 0 && (
        <Card variant="glass">
          <CardContent>
            <p className="text-slate-600">No seasonal profiles yet for this place.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
