import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  ArrowLeft, MapPin, Clock, Users, Star, Sparkles,
  CheckCircle2, AlertTriangle, ShieldCheck,
} from "lucide-react";
import { useState } from "react";
import { placesApi } from "@/api/places";
import { crowdApi, seasonApi } from "@/api/crowd";
import { visitsApi } from "@/api/visits";
import { communityApi } from "@/api/community";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonCard, Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { crowdMeta } from "@/lib/utils";

export function PlaceDetailPage() {
  const { placeId } = useParams<{ placeId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useToast();
  const [rating, setRating] = useState(4);
  const [comment, setComment] = useState("");
  const [showReview, setShowReview] = useState(false);

  const placeQ = useQuery({
    queryKey: ["places", "details", placeId],
    queryFn: () => placesApi.details(placeId!),
    enabled: !!placeId,
  });

  const crowdQ = useQuery({
    queryKey: ["crowd", placeId],
    queryFn: () => crowdApi.getForPlace(placeId!),
    enabled: !!placeId,
  });

  const seasonQ = useQuery({
    queryKey: ["season", placeId],
    queryFn: () => seasonApi.getForPlace(placeId!),
    enabled: !!placeId,
  });

  const reviewsQ = useQuery({
    queryKey: ["community", "reviews", placeId],
    queryFn: () => communityApi.listReviews(placeId!),
    enabled: !!placeId,
  });

  const visitMutation = useMutation({
    mutationFn: async () => {
      // Ask for GPS then verify
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error("Geolocation not supported by this browser."));
          return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 8000 });
      });
      return visitsApi.create({
        place_id: placeId!,
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
        timestamp: new Date().toISOString(),
      });
    },
    onSuccess: (visit) => {
      if (visit.status === "VERIFIED") {
        showToast({
          type: "success",
          title: "Visit verified!",
          message: `Distance ${visit.distance_from_place?.toFixed(0)}m · ${visit.visit_points_awarded} points`,
        });
      } else if (visit.status === "FLAGGED") {
        showToast({
          type: "warning",
          title: "Visit flagged for review",
          message: visit.rejection_reason || "Anti-cheat review pending.",
        });
      } else {
        showToast({
          type: "error",
          title: "Visit not verified",
          message: visit.rejection_reason || "Unknown reason",
        });
      }
    },
    onError: (err) => showToast({ type: "error", title: "Visit failed", message: errorMessage(err) }),
  });

  const reviewMutation = useMutation({
    mutationFn: () => communityApi.createReview({
      place_id: placeId!,
      rating,
      comment: comment.trim(),
    }),
    onSuccess: () => {
      showToast({ type: "success", title: "Review submitted", message: "Awaiting moderation." });
      setShowReview(false);
      setComment("");
      reviewsQ.refetch();
    },
    onError: (err) => showToast({ type: "error", title: "Review failed", message: errorMessage(err) }),
  });

  const place = placeQ.data;
  const cm = crowdMeta(crowdQ.data?.predicted_level || "MODERATE");
  const bestMonth = seasonQ.data?.best_month;

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-8">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-slate-900 transition"
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Back
      </button>

      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{place?.name || "Place details"}</h1>
        <p className="mt-1 text-slate-600">GET /api/places/details/{placeId}</p>
      </header>

      <Card variant="glass">
        <div className="relative h-64">
          <img
            src="https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1600&q=80"
            alt={place?.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
          <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center gap-2">
            {place?.types?.slice(0, 4).map((t) => <Badge key={t}>{t}</Badge>)}
          </div>
        </div>
        <CardContent>
          <p className="flex items-center gap-1 text-slate-700">
            <MapPin className="w-4 h-4 text-terracotta-600" aria-hidden="true" />
            {place?.address}
          </p>
          <p className="mt-2 flex items-center gap-1 text-slate-700">
            <Star className="w-4 h-4 fill-amber-400 text-amber-400" aria-hidden="true" />
            {place?.rating || "No rating"} · {place?.user_ratings_total || 0} reviews
          </p>

          {/* Crowd + season intel */}
          <div className="grid gap-4 sm:grid-cols-2 mt-6">
            <div className="rounded-2xl border-2 border-white/35 bg-white/80 p-4">
              <p className="text-sm font-semibold flex items-center gap-1">
                <Users className="w-4 h-4" aria-hidden="true" /> Crowd intelligence
              </p>
              {crowdQ.isLoading && <Skeleton className="h-4 w-32 mt-2" />}
              {crowdQ.data && (
                <div className="mt-2">
                  <span className={`inline-flex px-3 py-1 rounded-xl text-sm font-bold ${cm.bg} ${cm.color}`}>
                    {cm.label}
                  </span>
                  <p className="text-xs text-slate-500 mt-1">
                    Confidence {Math.round((crowdQ.data.confidence ?? 0) * 100)}% ·{" "}
                    {crowdQ.data.sample_count ?? 0} samples
                  </p>
                </div>
              )}
            </div>
            <div className="rounded-2xl border-2 border-white/35 bg-white/80 p-4">
              <p className="text-sm font-semibold flex items-center gap-1">
                <Clock className="w-4 h-4" aria-hidden="true" /> Seasonal score
              </p>
              {seasonQ.isLoading && <Skeleton className="h-4 w-32 mt-2" />}
              {bestMonth && (
                <div className="mt-2">
                  <span className="inline-flex px-3 py-1 rounded-xl bg-terracotta-100 text-terracotta-800 font-bold text-sm">
                    {bestMonth.overall_score}/100
                  </span>
                  <p className="text-xs text-slate-500 mt-1">
                    Best month · weather {bestMonth.weather_score}, crowd {bestMonth.crowd_score},
                    accessibility {bestMonth.accessibility_score}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Visit check-in */}
          <div className="mt-6 rounded-2xl border-2 border-white/35 bg-white/80 p-4">
            <p className="text-sm font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" /> GPS visit check-in
            </p>
            <p className="text-xs text-slate-500 mt-1">
              The backend verifies your GPS position with Haversine math and returns an
              authoritative status (VERIFIED / FLAGGED / REJECTED) — the UI never fakes this.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                onClick={() => visitMutation.mutate()}
                loading={visitMutation.isPending}
              >
                Check in here
              </Button>
              {showReview && (
                <Button size="sm" variant="outline" onClick={() => reviewMutation.mutate()} loading={reviewMutation.isPending}>
                  Submit review
                </Button>
              )}
            </div>
          </div>

          {/* Review form */}
          {showReview && (
            <Card className="mt-4">
              <CardContent>
                <CardTitle className="text-base">Leave a review</CardTitle>
                <CardDescription>POST /api/community/reviews</CardDescription>
                <div className="mt-3 space-y-3">
                  <div>
                    <span className="text-sm font-medium">Rating</span>
                    <div className="flex gap-1 mt-1" role="radiogroup">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <button
                          key={s}
                          onClick={() => setRating(s)}
                          className={`w-9 h-9 rounded-xl border-2 text-sm font-bold transition ${
                            rating === s ? "bg-amber-400 border-amber-400 text-black" : "border-slate-200 text-slate-500"
                          }`}
                          aria-label={`${s} stars`}
                          role="radio"
                          aria-checked={rating === s}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Share your experience…"
                    className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 min-h-[100px] focus:outline-none focus:border-terracotta-500"
                  />
                  <Button size="sm" onClick={() => reviewMutation.mutate()} loading={reviewMutation.isPending}>
                    Submit
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Reviews list */}
          <div className="mt-6">
            <CardTitle className="text-base">Reviews</CardTitle>
            {reviewsQ.isLoading && <SkeletonCard />}
            {reviewsQ.data && reviewsQ.data.length === 0 && (
              <p className="text-sm text-slate-500 mt-2">No reviews yet.</p>
            )}
            {reviewsQ.data?.map((r: any) => (
              <div key={r.id} className="mt-2 p-3 rounded-xl bg-slate-100/70">
                <div className="flex items-center gap-2">
                  <span className="text-amber-500">{"★".repeat(r.rating)}</span>
                  <Badge size="sm" variant={r.status === "APPROVED" ? "success" : "warning"}>{r.status}</Badge>
                </div>
                <p className="text-sm mt-1">{r.comment}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => visitMutation.mutate()} loading={visitMutation.isPending} variant="secondary">
          <CheckCircle2 className="w-4 h-4" aria-hidden="true" /> Verify visit
        </Button>
        <Button onClick={() => setShowReview(true)} variant="outline">
          Write a review
        </Button>
        <Button onClick={() => navigate("/crowd")} variant="ghost">
          <Users className="w-4 h-4" aria-hidden="true" /> Crowd forecast
        </Button>
        <Button onClick={() => navigate(`/season/${placeId}`)} variant="ghost">
          <Sparkles className="w-4 h-4" aria-hidden="true" /> Seasonal score
        </Button>
      </div>

      {placeQ.error && (
        <ErrorState
          title="Failed to load place"
          message={placeQ.error.message}
          onRetry={() => placeQ.refetch()}
        />
      )}
    </div>
  );
}
