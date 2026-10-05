import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Plane, Upload, CheckCircle2, AlertTriangle,
  ShieldCheck, Camera, XCircle, RefreshCw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { visitsApi } from "@/api/visits";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/utils";

export function VisitsPage() {
  const { showToast } = useToast();
  const fileRef = useRef<HTMLInputElement>(null);
  const [placeId, setPlaceId] = useState("demo_konark");
  const [selectedVisit, setSelectedVisit] = useState<number | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const visitsQ = useQuery({
    queryKey: ["visits"],
    queryFn: () => visitsApi.list(),
  });

  const checkinMutation = useMutation({
    mutationFn: async () => {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error("Geolocation unavailable."));
          return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 8000,
        });
      });
      return visitsApi.create({
        place_id: placeId,
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
          message: `${visit.visit_points_awarded} points awarded · distance ${visit.distance_from_place?.toFixed(1)}m`,
        });
      } else if (visit.status === "FLAGGED") {
        showToast({
          type: "warning",
          title: "Flagged for review",
          message: visit.rejection_reason || "Pending human review — not a ban.",
        });
      } else {
        showToast({
          type: "error",
          title: "Visit rejected",
          message: visit.rejection_reason || "Unknown reason",
        });
      }
      visitsQ.refetch();
    },
    onError: (err) => showToast({ type: "error", title: "Check-in failed", message: errorMessage(err) }),
  });

  const proofMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!selectedVisit) throw new Error("Select a visit first.");
      return visitsApi.uploadProof(selectedVisit, file);
    },
    onSuccess: (proof) => {
      if (proof.verification_status === "ACCEPTED") {
        showToast({
          type: "success",
          title: "Proof accepted!",
          message: `${proof.points_awarded} bonus points`,
        });
      } else if (proof.verification_status === "FLAGGED") {
        showToast({
          type: "warning",
          title: "Proof flagged",
          message: proof.rejection_reason || "Under review",
        });
      } else {
        showToast({
          type: "error",
          title: "Proof rejected",
          message: proof.rejection_reason || "Duplicate or invalid image",
        });
      }
      visitsQ.refetch();
    },
    onError: (err) => showToast({ type: "error", title: "Upload failed", message: errorMessage(err) }),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    proofMutation.mutate(file);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Visit verification</h1>
        <p className="mt-1 text-slate-600">POST /api/visits · POST /api/visits/{selectedVisit || "{id}"}/proof</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Check-in form */}
        <Card variant="glass">
          <CardContent>
            <CardTitle className="flex items-center gap-2">
              <Plane className="w-5 h-5 text-terracotta-600" aria-hidden="true" /> GPS check-in
            </CardTitle>
            <CardDescription>
              The backend verifies Haversine distance and returns authoritative status.
            </CardDescription>
            <div className="mt-4 space-y-4">
              <Input label="Place ID" value={placeId} onChange={(e) => setPlaceId(e.target.value)} />
              <Button
                onClick={() => checkinMutation.mutate()}
                loading={checkinMutation.isPending}
                fullWidth
                size="lg"
              >
                <ShieldCheck className="w-4 h-4" aria-hidden="true" /> Check in (use my GPS)
              </Button>
              {checkinMutation.data && (
                <div className={`rounded-2xl border-2 p-4 ${
                  checkinMutation.data.status === "VERIFIED"
                    ? "border-emerald-300 bg-emerald-50/70"
                    : checkinMutation.data.status === "FLAGGED"
                    ? "border-amber-300 bg-amber-50/70"
                    : "border-red-300 bg-red-50/70"
                }`}>
                  <p className="font-bold flex items-center gap-1">
                    {checkinMutation.data.status === "VERIFIED" && <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />}
                    {checkinMutation.data.status === "FLAGGED" && <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />}
                    {checkinMutation.data.status !== "VERIFIED" && checkinMutation.data.status !== "FLAGGED" && <XCircle className="w-4 h-4 text-red-600" aria-hidden="true" />}
                    Status: {checkinMutation.data.status}
                  </p>
                  <p className="text-sm mt-1">
                    Distance: {checkinMutation.data.distance_from_place?.toFixed(1)}m ·{" "}
                    Radius: {checkinMutation.data.verification_radius}m
                  </p>
                  {checkinMutation.data.rejection_reason && (
                    <p className="text-sm mt-1 text-slate-600">{checkinMutation.data.rejection_reason}</p>
                  )}
                  <p className="text-xs mt-1 text-slate-500">
                    Points: {checkinMutation.data.visit_points_awarded ?? 0} ·{" "}
                    Method: {checkinMutation.data.verification_method}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Proof upload */}
        <Card variant="glass">
          <CardContent>
            <CardTitle className="flex items-center gap-2">
              <Camera className="w-5 h-5" aria-hidden="true" /> Photo proof
            </CardTitle>
            <CardDescription>
              Upload a real photo — hashed for duplicate detection. Select a visit above first.
            </CardDescription>
            <div className="mt-4 space-y-3">
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                onChange={handleFileChange}
                className="hidden"
                aria-label="Photo proof file"
              />
              <Button
                onClick={() => fileRef.current?.click()}
                disabled={!selectedVisit || proofMutation.isPending}
                loading={proofMutation.isPending}
                fullWidth
                variant="secondary"
                size="lg"
              >
                <Upload className="w-4 h-4" aria-hidden="true" /> {proofMutation.isPending ? "Uploading…" : "Upload proof"}
              </Button>
              {!selectedVisit && (
                <p className="text-xs text-slate-500">⚠ Select a visit from the list first.</p>
              )}
              {preview && (
                <img src={preview} alt="Proof preview" className="rounded-2xl border-2 border-white/40 max-h-48 w-full object-cover" />
              )}
              {proofMutation.data && (
                <div className={`rounded-2xl border-2 p-4 ${
                  proofMutation.data.verification_status === "ACCEPTED"
                    ? "border-emerald-300 bg-emerald-50/70"
                    : "border-amber-300 bg-amber-50/70"
                }`}>
                  <p className="font-bold">Proof: {proofMutation.data.verification_status}</p>
                  {proofMutation.data.rejection_reason && (
                    <p className="text-sm mt-1 text-slate-600">{proofMutation.data.rejection_reason}</p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Visit history */}
      <section aria-label="Visit history">
        <h2 className="text-2xl font-extrabold tracking-tight">Your visits</h2>
        {visitsQ.isLoading && <SkeletonTable rows={3} cols={4} />}
        {visitsQ.data && visitsQ.data.items.length === 0 && (
          <EmptyState icon={Plane} title="No visits yet" description="Check in at a place to get started." />
        )}
        {visitsQ.data && visitsQ.data.items.length > 0 && (
          <div className="mt-4 space-y-2">
            {visitsQ.data.items.map((v) => (
              <Card
                key={v.id}
                variant={selectedVisit === v.id ? "default" : "glass"}
                interactive
                onClick={() => setSelectedVisit(v.id)}
                className={selectedVisit === v.id ? "ring-2 ring-terracotta-600" : ""}
              >
                <CardContent className="flex flex-wrap items-center gap-3 py-4">
                  <Badge variant={v.status === "VERIFIED" ? "success" : v.status === "FLAGGED" ? "warning" : "danger"}>
                    {v.status}
                  </Badge>
                  <p className="font-semibold flex-1 min-w-[120px]">{v.place_id}</p>
                  <p className="text-sm text-slate-500 flex items-center gap-1">
                    <Plane className="w-3.5 h-3.5" aria-hidden="true" />
                    {v.distance_from_place?.toFixed(1)}m
                  </p>
                  <p className="text-sm text-slate-500">{formatDate(v.timestamp)}</p>
                  <Badge variant="info">{v.visit_points_awarded ?? 0} pts</Badge>
                  {v.rejection_reason && (
                    <Badge variant="warning">
                      {v.rejection_reason}
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
