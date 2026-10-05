import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Sparkles, Calendar, MapPin, Clock, Users, Sun } from "lucide-react";
import { plannerApi } from "@/api/planner";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ErrorState } from "@/components/ui/ErrorState";
import { crowdMeta } from "@/lib/utils";

const DEMO_PLACES = [
  { id: "demo_konark", label: "Konark Sun Temple" },
  { id: "demo_puri", label: "Puri Beach" },
  { id: "demo_chilika", label: "Chilika Lake" },
  { id: "demo_bhubaneswar", label: "Bhubaneswar" },
];

const DEFAULT_PREFS = {
  temples: true,
  nature: true,
  food: true,
  beaches: false,
  culture: true,
  shopping: false,
  adventure: false,
  family_friendly: true,
};

export function ItineraryPage() {
  const { showToast } = useToast();
  const [origin, setOrigin] = useState("Bhubaneswar");
  const [destinations, setDestinations] = useState<string[]>(["demo_konark", "demo_puri"]);
  const [days, setDays] = useState(2);
  const [budget, setBudget] = useState(480);
  const [startHour, setStartHour] = useState(9);
  const [endHour, setEndHour] = useState(18);
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [prefs, setPrefs] = useState({ ...DEFAULT_PREFS });
  const [result, setResult] = useState<any>(null);
  const [aiEnabled, setAiEnabled] = useState(false);

  const generateMutation = useMutation({
    mutationFn: async () => {
      const data = await plannerApi.generate({
        start_location: { latitude: 20.2961, longitude: 85.8245 },
        destinations,
        available_hours: Number((budget / 60).toFixed(1)),
        days,
        start_time: `${String(startHour).padStart(2, '0')}:00`,
        start_date: date,
        visit_duration_minutes: 90,
        return_to_start: true,
        preferences: prefs,
      });
      return data;
    },
    onSuccess: (data) => {
      setResult(data);
      showToast({
        type: "success",
        title: "Itinerary generated",
        message: `${data.days?.length || 0} day(s) planned with crowd-aware scheduling.`,
      });
    },
    onError: (err) => showToast({ type: "error", title: "Generation failed", message: errorMessage(err) }),
  });

  const explainMutation = useMutation({
    mutationFn: () => plannerApi.explain(result),
    onSuccess: (res) => {
      setAiEnabled(res.enabled);
      showToast({
        type: "success",
        title: res.enabled ? "AI explanation ready" : "Deterministic fallback",
        message: res.explanation.slice(0, 80),
      });
    },
    onError: (err) => showToast({ type: "error", title: "Explain failed", message: errorMessage(err) }),
  });

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">AI itinerary planner</h1>
        <p className="mt-1 text-slate-600">POST /api/planner/generate · POST /api/planner/explain</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Controls */}
        <Card variant="glass">
          <CardContent className="space-y-4">
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-5 h-5" aria-hidden="true" /> Trip parameters
            </CardTitle>
            <Input label="Origin" value={origin} onChange={(e) => setOrigin(e.target.value)} />
            <div>
              <label className="block text-sm font-medium mb-1.5">Destinations</label>
              <div className="space-y-1.5">
                {DEMO_PLACES.map((p) => (
                  <label key={p.id} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={destinations.includes(p.id)}
                      onChange={(e) =>
                        setDestinations(e.target.checked ? [...destinations, p.id] : destinations.filter((d) => d !== p.id))
                      }
                      className="w-4 h-4 rounded accent-terracotta-600"
                    />
                    {p.label}
                  </label>
                ))}
              </div>
            </div>
            <Input label="Days" type="number" min={1} max={7} value={days} onChange={(e) => setDays(Number(e.target.value))} />
            <Input label="Time budget (min/day)" type="number" value={budget} onChange={(e) => setBudget(Number(e.target.value))} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Start hour" type="number" min={0} max={23} value={startHour} onChange={(e) => setStartHour(Number(e.target.value))} />
              <Input label="End hour" type="number" min={0} max={23} value={endHour} onChange={(e) => setEndHour(Number(e.target.value))} />
            </div>
            <Input label="Start date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            <div>
              <span className="text-sm font-medium">Preferences</span>
              <div className="mt-1.5 grid grid-cols-2 gap-1.5">
                {Object.keys(prefs).map((key) => (
                  <label key={key} className="flex items-center gap-2 text-sm cursor-pointer capitalize">
                    <input
                      type="checkbox"
                      checked={(prefs as any)[key]}
                      onChange={(e) => setPrefs({ ...prefs, [key]: e.target.checked })}
                      className="w-4 h-4 rounded accent-terracotta-600"
                    />
                    {key.replace(/_/g, " ")}
                  </label>
                ))}
              </div>
            </div>
            <Button
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
              fullWidth
              size="lg"
            >
              <Sparkles className="w-4 h-4" aria-hidden="true" /> Generate itinerary
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {generateMutation.error && (
            <ErrorState title="Planning failed" message={generateMutation.error.message} onRetry={() => generateMutation.mutate()} />
          )}

          {!result && !generateMutation.isPending && (
            <Card variant="glass">
              <CardContent>
                <p className="text-slate-600 text-center py-12">
                  Configure your trip and hit <strong>Generate itinerary</strong>.
                  <br />
                  The backend schedules places using crowd data, opening hours and travel times.
                </p>
              </CardContent>
            </Card>
          )}

          {generateMutation.isPending && (
            <Card variant="glass">
              <CardContent className="py-12 text-center">
                <div className="w-12 h-12 border-4 border-terracotta-600 border-t-transparent rounded-full animate-spin mx-auto" aria-hidden="true" />
                <p className="mt-4 text-slate-600">Planning with crowd intelligence…</p>
              </CardContent>
            </Card>
          )}

          {result && (
            <>
              <Card variant="glass">
                <CardContent className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <CardTitle>Itinerary summary</CardTitle>
                    <CardDescription>
                      {result.days?.length} days · total{" "}
                      {Math.round((result.estimated_total_duration_minutes ?? 0) / 60)}h travel ·{" "}
                      {((result.estimated_total_distance_meters ?? 0) / 1000).toFixed(0)} km
                    </CardDescription>
                  </div>
                  <Button onClick={() => explainMutation.mutate()} loading={explainMutation.isPending} variant="secondary">
                    <Sparkles className="w-4 h-4" aria-hidden="true" /> Explain with AI
                  </Button>
                </CardContent>
                {explainMutation.data && (
                  <div className="px-6 pb-5">
                    <div className={`rounded-2xl border-2 p-4 ${explainMutation.data.enabled ? "border-terracotta-300 bg-terracotta-50/60" : "border-slate-200 bg-slate-50"}`}>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        {explainMutation.data.enabled ? "AI explanation" : "Deterministic fallback explanation"}
                      </p>
                      <p className="mt-2 text-slate-700 whitespace-pre-line">{explainMutation.data.explanation}</p>
                    </div>
                  </div>
                )}
              </Card>

              {result.days?.map((day: any) => (
                <Card key={day.day} variant="glass">
                  <CardContent>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-terracotta-600" aria-hidden="true" /> Day {day.day}
                    </CardTitle>
                    <CardDescription>
                      {day.items?.length} places ·{" "}
                      {Math.round((day.total_travel_minutes ?? 0))}m travel ·{" "}
                      {Math.round((day.total_place_minutes ?? 0))}m visiting
                    </CardDescription>
                    <div className="mt-4 space-y-3">
                      {day.items?.map((item: any, idx: number) => {
                        const cm = crowdMeta(item.crowd_level || "MODERATE");
                        return (
                          <div key={idx} className="rounded-2xl border-2 border-white/40 bg-white/80 p-4">
                            <div className="flex items-start justify-between gap-3 flex-wrap">
                              <div>
                                <p className="font-bold text-lg">{item.place?.name}</p>
                                <p className="text-sm text-slate-500 flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5" aria-hidden="true" />
                                  {item.start} → {item.end} · {item.duration_minutes}m
                                  {item.travel_in_seconds ? (
                                    <> · {Math.round(item.travel_in_seconds / 60)}m travel</>
                                  ) : null}
                                </p>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                <Badge variant="default">{item.opening_status || "Open"}</Badge>
                                {item.crowd_level && (
                                  <Badge className={cm.color} variant="outline">
                                    <span className={`w-2 h-2 rounded-full ${cm.dot}`} aria-hidden="true" />
                                    {cm.label}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            {item.place?.types?.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {item.place.types.slice(0, 4).map((t: string) => (
                                  <span key={t} className="text-xs px-2 py-0.5 rounded-md bg-slate-100">{t}</span>
                                ))}
                              </div>
                            )}
                            {item.reasoning && (
                              <p className="mt-2 text-sm text-slate-600 flex items-start gap-1">
                                <Sun className="w-4 h-4 mt-0.5 text-amber-500 shrink-0" aria-hidden="true" />
                                {item.reasoning}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    {day.return_leg_seconds != null && (
                      <p className="mt-3 text-sm text-slate-500 flex items-center gap-1">
                        <MapPin className="w-4 h-4" aria-hidden="true" />
                        Return leg: {Math.round(day.return_leg_seconds / 60)} min
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
