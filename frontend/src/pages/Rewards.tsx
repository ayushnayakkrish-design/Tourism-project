import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Gift, Coins, CheckCircle2, AlertTriangle,
  Tag, Package, Clock,
} from "lucide-react";
import { rewardsApi } from "@/api/rewards";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { formatPoints, formatDate } from "@/lib/utils";

export function RewardsPage() {
  const { showToast } = useToast();
  const [selectedReward, setSelectedReward] = useState<number | null>(null);
  const [code, setCode] = useState<string | null>(null);
  const [category, setCategory] = useState("");

  const rewardsQ = useQuery({
    queryKey: ["rewards", category],
    queryFn: () => rewardsApi.list(category ? { category } : undefined),
  });

  const redemptionsQ = useQuery({
    queryKey: ["redemptions"],
    queryFn: () => rewardsApi.myRedemptions({ page: 1, page_size: 10 }),
  });

  const redeemMutation = useMutation({
    mutationFn: (rewardId: number) => rewardsApi.redeem(rewardId),
    onSuccess: (redemption) => {
      setCode(redemption.redemption_code);
      showToast({ type: "success", title: "Redeemed!", message: `Code: ${redemption.redemption_code}` });
      rewardsQ.refetch();
      redemptionsQ.refetch();
    },
    onError: (err) => showToast({ type: "error", title: "Redemption failed", message: errorMessage(err) }),
  });

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Rewards catalog</h1>
        <p className="mt-1 text-slate-600">GET /api/rewards · POST /api/rewards/:id/redeem · GET /api/redemptions</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {/* Category filter */}
          <div className="flex flex-wrap gap-2">
            {["", "souvenir", "experience", "discount"].map((cat) => (
              <button
                key={cat || "all"}
                onClick={() => setCategory(cat)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition ${
                  category === cat ? "bg-black text-white" : "bg-white/70 border-2 border-slate-200 hover:bg-slate-100"
                }`}
              >
                {cat === "" ? "All" : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>

          {rewardsQ.isLoading && <SkeletonTable rows={3} cols={3} />}

          {rewardsQ.data && rewardsQ.data.items.length === 0 && (
            <EmptyState icon={Gift} title="No rewards available" description="Check back soon for new rewards." />
          )}

          <div className="grid gap-4 sm:grid-cols-2 stagger">
            {rewardsQ.data?.items.map((r) => (
              <Card key={r.id} variant="glass" interactive>
                <CardContent>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-lg flex items-center gap-1">
                        <Tag className="w-4 h-4 text-terracotta-600" aria-hidden="true" />
                        {r.name}
                      </p>
                      <p className="text-sm text-slate-500">{r.provider}</p>
                    </div>
                    <Badge variant="default">{r.category}</Badge>
                  </div>
                  <p className="mt-3 text-sm text-slate-600 line-clamp-2">{r.description}</p>
                  <div className="mt-3 flex items-center gap-3 text-sm">
                    <span className="flex items-center gap-1 text-amber-600 font-semibold">
                      <Coins className="w-4 h-4" aria-hidden="true" /> {formatPoints(r.points_required)}
                    </span>
                    <span className="flex items-center gap-1 text-slate-500">
                      <Package className="w-4 h-4" aria-hidden="true" />
                      {r.stock != null ? `${r.stock} in stock` : "unlimited"}
                    </span>
                    {r.expires_at && (
                      <span className="flex items-center gap-1 text-slate-500">
                        <Clock className="w-4 h-4" aria-hidden="true" /> {formatDate(r.expires_at)}
                      </span>
                    )}
                  </div>
                  <Button
                    size="sm"
                    className="mt-4"
                    onClick={() => { setSelectedReward(r.id); redeemMutation.mutate(r.id); }}
                    loading={redeemMutation.isPending && selectedReward === r.id}
                  >
                    <Gift className="w-4 h-4" aria-hidden="true" /> Redeem
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Redemptions */}
        <Card variant="glass">
          <CardContent>
            <CardTitle>Your redemptions</CardTitle>
            <CardDescription>GET /api/redemptions</CardDescription>
            {redemptionsQ.isLoading && <SkeletonTable rows={3} cols={2} />}
            {redemptionsQ.data && redemptionsQ.data.items.length === 0 && (
              <EmptyState icon={Gift} title="No redemptions yet" description="Redeem your first reward!" />
            )}
            {redemptionsQ.data?.items.map((red) => (
              <div key={red.id} className="mt-2 p-3 rounded-xl bg-white/80 border border-white/40">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-sm">{red.reward_name || `Reward #${red.reward_id}`}</p>
                  <Badge variant={red.status === "ACTIVE" ? "success" : "default"}>{red.status}</Badge>
                </div>
                <p className="text-sm text-amber-600 font-mono mt-1">{red.redemption_code}</p>
                <p className="text-xs text-slate-500">{formatDate(red.created_at)} · {red.points_spent} pts</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Redemption code modal */}
      <Modal isOpen={!!code} onClose={() => setCode(null)} title="Redemption code" size="sm">
        <div className="text-center py-6">
          <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto" aria-hidden="true" />
          <p className="mt-4 text-slate-600">Your unique redemption code:</p>
          <p className="mt-2 text-3xl font-mono font-bold text-terracotta-700 bg-slate-100 rounded-2xl px-6 py-4">
            {code}
          </p>
          <Button className="mt-4" onClick={() => setCode(null)}>Done</Button>
        </div>
      </Modal>
    </div>
  );
}
