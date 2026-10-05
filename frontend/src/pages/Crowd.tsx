import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Users, TrendingUp, Lightbulb } from "lucide-react";
import { crowdApi } from "@/api/crowd";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { crowdMeta } from "@/lib/utils";

export function CrowdPage() {
  const { placeId } = useParams<{ placeId: string }>();
  const targetPlace = placeId || "demo_konark";

  const crowdQ = useQuery({
    queryKey: ["crowd", targetPlace],
    queryFn: () => crowdApi.getForPlace(targetPlace),
  });

  const data = crowdQ.data;

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Crowd intelligence</h1>
        <p className="mt-1 text-slate-600">GET /api/crowd/{targetPlace} · historical-weighted prediction</p>
      </header>

      {crowdQ.isLoading && <SkeletonCard />}

      {data && (
        <>
          <Card variant="glass">
            <CardContent>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-500">Current predicted level</p>
                  <p className="text-4xl font-extrabold mt-1">
                    {(() => {
                      const cm = crowdMeta(data.predicted_level || "MODERATE");
                      return <span className={cm.color}>{cm.label}</span>;
                    })()}
                  </p>
                  <p className="text-sm text-slate-500 mt-1">
                    Confidence {Math.round((data.confidence ?? 0) * 100)}% · {data.sample_count ?? 0} samples
                  </p>
                </div>
                <div className="w-24 h-24 rounded-full border-4 border-slate-200 flex items-center justify-center">
                  <span className="text-2xl font-extrabold">
                    {Math.round((data.confidence ?? 0) * 100)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card variant="glass">
            <CardContent>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" aria-hidden="true" /> Best time slots today
              </CardTitle>
              <CardDescription>Weighted recency + historical match.</CardDescription>
              <div className="mt-4 space-y-2">
                {data.best_time_slots?.slice(0, 8).map((slot) => {
                  const cm = crowdMeta(slot.predicted_level);
                  return (
                    <div
                      key={slot.hour}
                      className="flex items-center gap-3 p-3 rounded-xl bg-white/80 border border-white/40"
                    >
                      <span className="font-mono font-semibold text-sm w-14">
                        {String(slot.hour).padStart(2, "0")}:00
                      </span>
                      <div className="flex-1">
                        <div className="h-2.5 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${cm.dot}`}
                            style={{ width: `${Math.round((slot.confidence || 0) * 100)}%` }}
                            aria-hidden="true"
                          />
                        </div>
                      </div>
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${cm.bg} ${cm.color}`}>
                        {cm.label}
                      </span>
                      <span className="text-xs text-slate-500 w-16 text-right">
                        {Math.round((slot.confidence || 0) * 100)}% conf
                      </span>
                    </div>
                  );
                })}
                {(!data.best_time_slots || data.best_time_slots.length === 0) && (
                  <EmptyState
                    icon={Users}
                    title="No slot recommendations"
                    description="More observations are needed for this place."
                    className="py-8"
                  />
                )}
              </div>
            </CardContent>
          </Card>

          <Card variant="glass">
            <CardContent>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5" aria-hidden="true" /> How to read this
              </CardTitle>
              <ul className="mt-3 space-y-1.5 text-sm text-slate-600 list-disc list-inside">
                <li>Levels come from real backend crowd observations, not mock data.</li>
                <li>Confidence reflects sample size and recency weighting.</li>
                <li>Best slots are computed by the predictor service (hour + weekday match).</li>
                <li>Itinerary planning uses these signals to avoid crowds when possible.</li>
              </ul>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
