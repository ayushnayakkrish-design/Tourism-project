import { useState } from "react";
import { Route, MapPin, Navigation, Clock } from "lucide-react";
import { routesApi } from "@/api/places";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ErrorState } from "@/components/ui/ErrorState";

const DEMO_PLACES = [
  { label: "Konark Sun Temple", latitude: 19.8876, longitude: 86.0945 },
  { label: "Puri Beach", latitude: 19.7983, longitude: 85.8249 },
  { label: "Lingaraj Temple", latitude: 20.2356, longitude: 85.8321 },
  { label: "Bhubaneswar Airport", latitude: 20.2444, longitude: 85.8178 },
];

export function RoutesPage() {
  const { showToast } = useToast();
  const [originLat, setOriginLat] = useState("20.2961");
  const [originLng, setOriginLng] = useState("85.8245");
  const [destLat, setDestLat] = useState("19.8876");
  const [destLng, setDestLng] = useState("86.0945");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const compute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await routesApi.route(
        { latitude: parseFloat(originLat), longitude: parseFloat(originLng) },
        { latitude: parseFloat(destLat), longitude: parseFloat(destLng) }
      );
      setResult(data);
      showToast({ type: "success", title: "Route computed", message: "Traffic-aware response received." });
    } catch (err) {
      setError(errorMessage(err));
      showToast({ type: "error", title: "Routing failed", message: errorMessage(err) });
    } finally {
      setLoading(false);
    }
  };

  const applyPlace = (which: "origin" | "dest", lat: string, lng: string) => {
    if (which === "origin") {
      setOriginLat(lat); setOriginLng(lng);
    } else {
      setDestLat(lat); setDestLng(lng);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Routes & directions</h1>
        <p className="mt-1 text-slate-600">POST /api/routes/route · traffic-aware Google Routes</p>
      </header>

      <Card variant="glass">
        <CardContent>
          <CardTitle className="flex items-center gap-2">
            <Route className="w-5 h-5" aria-hidden="true" /> Compute a route
          </CardTitle>
          <CardDescription>Origin & destination coordinates — validated by the backend.</CardDescription>

          <div className="grid gap-6 md:grid-cols-2 mt-6">
            {/* Origin */}
            <div className="space-y-3">
              <p className="text-sm font-semibold flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-emerald-500" aria-hidden="true" /> Origin
              </p>
              <Input label="Latitude" type="number" value={originLat} onChange={(e) => setOriginLat(e.target.value)} />
              <Input label="Longitude" type="number" value={originLng} onChange={(e) => setOriginLng(e.target.value)} />
              <div className="flex flex-wrap gap-1.5">
                {DEMO_PLACES.map((p) => (
                  <button
                    key={`o-${p.label}`}
                    onClick={() => applyPlace("origin", p.latitude.toString(), p.longitude.toString())}
                    className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 transition"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Destination */}
            <div className="space-y-3">
              <p className="text-sm font-semibold flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-terracotta-600" aria-hidden="true" /> Destination
              </p>
              <Input label="Latitude" type="number" value={destLat} onChange={(e) => setDestLat(e.target.value)} />
              <Input label="Longitude" type="number" value={destLng} onChange={(e) => setDestLng(e.target.value)} />
              <div className="flex flex-wrap gap-1.5">
                {DEMO_PLACES.map((p) => (
                  <button
                    key={`d-${p.label}`}
                    onClick={() => applyPlace("dest", p.latitude.toString(), p.longitude.toString())}
                    className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 transition"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Button onClick={compute} loading={loading} className="mt-6" size="lg">
            <Navigation className="w-4 h-4" aria-hidden="true" /> Compute Route
          </Button>
        </CardContent>
      </Card>

      {error && <ErrorState title="Routing unavailable" message={error} onRetry={compute} />}

      {result && (
        <Card variant="glass">
          <CardContent>
            <CardTitle>Route details</CardTitle>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {result.routes?.[0]?.legs?.map((leg: any, i: number) => (
                <div key={i} className="rounded-2xl border-2 border-white/35 bg-white/80 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="info">Leg {i + 1}</Badge>
                    <Badge variant="default">{leg.travel_mode || "DRIVE"}</Badge>
                  </div>
                  <p className="flex items-center gap-1 text-sm">
                    <Clock className="w-4 h-4 text-terracotta-600" aria-hidden="true" />
                    <span className="font-semibold">{Math.round((leg.duration_seconds || 0) / 60)} min</span>
                    (static: {Math.round((leg.static_duration_seconds || 0) / 60)} min)
                  </p>
                  <p className="flex items-center gap-1 text-sm">
                    <Navigation className="w-4 h-4 text-terracotta-600" aria-hidden="true" />
                    <span className="font-semibold">{((leg.distance_meters || 0) / 1000).toFixed(1)} km</span>
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
