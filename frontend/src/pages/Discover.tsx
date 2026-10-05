import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import {
  Search, MapPin, Compass, SlidersHorizontal,
  Clock, Users, Star, Sparkles, ArrowRight,
} from "lucide-react";
import { placesApi } from "@/api/places";
import { crowdApi } from "@/api/crowd";
import { useDebounced } from "@/hooks/useData";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonCard, SkeletonTable } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { crowdMeta } from "@/lib/utils";

export function DiscoverPage() {
  const [q, setQ] = useState("");
  const debouncedQ = useDebounced(q, 400);
  const canSearch = debouncedQ.trim().length >= 2;

  const searchQ = useQuery({
    queryKey: ["places", "search", debouncedQ],
    queryFn: () => placesApi.search(debouncedQ.trim()),
    enabled: canSearch,
    placeholderData: keepPreviousData,
  });

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Discover places</h1>
        <p className="mt-1 text-slate-600">GET /api/places/search · real-time results from backend</p>
      </header>

      <Card variant="glass">
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
            <div className="flex-1 w-full">
              <Input
                label="Search places"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="e.g. Konark Sun Temple, Puri Beach, Chilika Lake"
              />
            </div>
            <Button
              onClick={() => setQ(q)}
              disabled={!canSearch}
              className="w-full sm:w-auto"
            >
              <Compass className="w-4 h-4" aria-hidden="true" /> Search
            </Button>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Minimum 2 characters. Results returned by Developer 1 Places API.
          </p>
        </CardContent>
      </Card>

      {searchQ.isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {searchQ.error && (
        <ErrorState
          title="Search failed"
          message={searchQ.error.message}
          onRetry={() => searchQ.refetch()}
        />
      )}

      {!searchQ.isFetched && (
        <EmptyState
          icon={SlidersHorizontal}
          title="Type a destination"
          description="Search by name, type, or attraction. We'll show crowd intel, types and coordinates."
        />
      )}

      {searchQ.data && searchQ.data.places.length === 0 && (
        <EmptyState
          icon={MapPin}
          title="No places found"
          description="Try a broader query — e.g. temples, beaches, restaurants."
        />
      )}

      {searchQ.data && searchQ.data.places.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 stagger">
          {searchQ.data.places.map((p) => (
            <PlaceCard key={p.place_id} place={p} />
          ))}
        </div>
      )}
    </div>
  );
}

function PlaceCard({ place }: { place: any }) {
  const crowdQ = useQuery({
    queryKey: ["crowd", place.place_id, "24h"],
    queryFn: () => crowdApi.getForPlace(place.place_id),
    staleTime: 60_000,
  });

  const cm = crowdMeta(crowdQ.data?.predicted_level || "MODERATE");

  return (
    <Link to={`/places/${place.place_id}`}>
      <Card variant="glass" interactive>
        <div className="relative h-48 overflow-hidden">
          <img
            src="https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=900&q=80"
            alt={place.name}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
          <div className="absolute top-3 left-3 flex flex-wrap gap-2">
            {place.types?.slice(0, 2).map((t: string) => (
              <Badge key={t} size="sm">{t}</Badge>
            ))}
          </div>
          {crowdQ.data?.predicted_level && (
            <span className={`absolute top-3 right-3 text-xs font-semibold px-3 py-1 rounded-full backdrop-blur ${cm.bg} ${cm.color}`}>
              {cm.label} (now)
            </span>
          )}
          <div className="absolute bottom-3 left-4 right-4 text-white">
            <h3 className="text-lg font-bold line-clamp-1">{place.name}</h3>
            <p className="text-sm opacity-90 flex items-center gap-1 line-clamp-1">
              <MapPin className="w-3.5 h-3.5" aria-hidden="true" /> {place.address || place.place_id}
            </p>
          </div>
        </div>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span className="flex items-center gap-1">
              <Users className="w-4 h-4" aria-hidden="true" />
              Crowd {crowdQ.data ? `${Math.round((crowdQ.data.confidence ?? 0) * 100)}% conf.` : "checking…"}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" aria-hidden="true" />
              Best time in view
            </span>
          </div>
          <p className="mt-3 text-sm text-slate-700 line-clamp-2">
            Explore opening hours, seasonal scores, crowd predictions and reviews.
          </p>
          <div className="mt-4 flex items-center justify-between">
            <span className="flex items-center gap-1 text-sm text-amber-600">
              <Star className="w-4 h-4 fill-amber-400" aria-hidden="true" /> Verified backend data
            </span>
            <span className="text-sm font-semibold text-terracotta-700 flex items-center gap-1">
              View details <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
