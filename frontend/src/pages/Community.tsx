import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Users, MapPin, Camera, MessageSquare, Plus,
  CheckCircle2, Clock, XCircle, Send,
} from "lucide-react";
import { communityApi } from "@/api/community";
import { useToast } from "@/hooks/useToast";
import { useAuth } from "@/hooks/useAuth";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/utils";

export function CommunityPage() {
  const { showToast } = useToast();
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [type, setType] = useState("restaurant");
  const [name, setName] = useState("");
  const [lat, setLat] = useState("19.8876");
  const [lng, setLng] = useState("86.0945");
  const [description, setDescription] = useState("");
  const [photos, setPhotos] = useState("");
  const [language, setLanguage] = useState("en");

  const submissionsQ = useQuery({
    queryKey: ["community", "submissions"],
    queryFn: () => communityApi.listSubmissions(),
  });

  const mineQ = useQuery({
    queryKey: ["community", "mine"],
    queryFn: () => communityApi.mySubmissions(),
  });

  const submitMutation = useMutation({
    mutationFn: () => communityApi.createSubmission({
      type,
      name: name.trim(),
      latitude: parseFloat(lat),
      longitude: parseFloat(lng),
      description: description.trim(),
      photos: photos.split(",").map((s) => s.trim()).filter(Boolean),
      language,
    }),
    onSuccess: (sub) => {
      showToast({ type: "success", title: "Submitted!", message: "Awaiting moderator review." });
      setShowForm(false);
      setName("");
      setDescription("");
      setPhotos("");
      submissionsQ.refetch();
      mineQ.refetch();
    },
    onError: (err) => showToast({ type: "error", title: "Submission failed", message: errorMessage(err) }),
  });

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Community</h1>
          <p className="mt-1 text-slate-600">POST/GET /api/community/places · moderated public submissions</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4" aria-hidden="true" /> Submit a place
        </Button>
      </header>

      {showForm && (
        <Card variant="glass">
          <CardContent>
            <CardTitle>Submit a community place</CardTitle>
            <CardDescription>Goes through moderation before becoming public.</CardDescription>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium mb-1.5">Type</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90 focus:outline-none focus:border-terracotta-500"
                >
                  {["restaurant", "attraction", "hotel", "cafe", "temple", "other"].map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Place name" />
              <Input label="Latitude" type="number" value={lat} onChange={(e) => setLat(e.target.value)} />
              <Input label="Longitude" type="number" value={lng} onChange={(e) => setLng(e.target.value)} />
              <Textarea
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the place, highlights, best time to visit…"
                rows={3}
              />
              <Input
                label="Photo URLs (comma separated)"
                value={photos}
                onChange={(e) => setPhotos(e.target.value)}
                placeholder="https://…"
              />
              <div>
                <label className="block text-sm font-medium mb-1.5">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-4 py-3 rounded-2xl border-2 border-slate-200/80 bg-white/90"
                >
                  <option value="en">English</option>
                  <option value="hi">हिन्दी</option>
                  <option value="or">ଓଡ଼ିଆ</option>
                </select>
              </div>
            </div>
            <Button
              onClick={() => submitMutation.mutate()}
              loading={submitMutation.isPending}
              className="mt-4"
            >
              <Send className="w-4 h-4" aria-hidden="true" /> Submit for review
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Public submissions */}
      <section aria-label="Approved places">
        <h2 className="text-2xl font-extrabold tracking-tight">Approved places</h2>
        {submissionsQ.isLoading && <SkeletonTable rows={3} cols={3} />}
        {submissionsQ.data && submissionsQ.data.length === 0 && (
          <EmptyState icon={Users} title="No places yet" description="Be the first to share a hidden gem!" />
        )}
        {submissionsQ.data && submissionsQ.data.length > 0 && (
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger">
            {submissionsQ.data.map((sub) => (
              <Card key={sub.id} variant="glass">
                <div className="relative h-32">
                  <img
                    src={sub.photos?.[0] || "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=600&q=80"}
                    alt={sub.name}
                    className="w-full h-full object-cover"
                  />
                  <Badge className="absolute top-2 left-2" size="sm">{sub.type}</Badge>
                </div>
                <CardContent>
                  <h3 className="font-bold">{sub.name}</h3>
                  <p className="text-sm text-slate-500 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" aria-hidden="true" /> {sub.latitude}, {sub.longitude}
                  </p>
                  <p className="mt-2 text-sm text-slate-600 line-clamp-2">{sub.description}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <Badge
                      variant={sub.status === "APPROVED" ? "success" : sub.status === "PENDING" ? "warning" : "danger"}
                      dot
                    >
                      {sub.status}
                    </Badge>
                    <span className="text-xs text-slate-400">{formatDate(sub.created_at)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* My submissions */}
      <section aria-label="My submissions">
        <h2 className="text-2xl font-extrabold tracking-tight">My submissions</h2>
        {mineQ.data && mineQ.data.length > 0 && (
          <div className="mt-4 space-y-2">
            {mineQ.data.map((sub) => (
              <Card key={sub.id} variant="glass">
                <CardContent className="flex flex-wrap items-center gap-3 py-3">
                  <Badge
                    variant={sub.status === "APPROVED" ? "success" : sub.status === "PENDING" ? "warning" : "danger"}
                    dot
                  >
                    {sub.status}
                  </Badge>
                  <span className="font-semibold">{sub.name}</span>
                  <span className="text-sm text-slate-500">{sub.type}</span>
                  {sub.moderator_note && (
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" aria-hidden="true" /> {sub.moderator_note}
                    </span>
                  )}
                  <span className="ml-auto text-xs text-slate-400">{formatDate(sub.created_at)}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
