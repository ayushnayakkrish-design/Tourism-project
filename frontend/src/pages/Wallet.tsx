import { useQuery } from "@tanstack/react-query";
import { Wallet, TrendingUp, TrendingDown, Coins, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { walletApi } from "@/api/rewards";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { formatPoints, formatDate } from "@/lib/utils";

export function WalletPage() {
  const walletQ = useQuery({ queryKey: ["wallet"], queryFn: () => walletApi.get() });
  const txQ = useQuery({
    queryKey: ["wallet", "transactions"],
    queryFn: () => walletApi.transactions({ page: 1, page_size: 20 }),
  });

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Wallet & points</h1>
        <p className="mt-1 text-slate-600">GET /api/wallet · GET /api/points/transactions</p>
      </header>

      {/* Balance card */}
      <div className="relative rounded-[2rem] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-terracotta-600 via-terracotta-500 to-amber-500" aria-hidden="true" />
        <div className="absolute -top-10 -right-10 w-56 h-56 rounded-full bg-white/20 blur-2xl" aria-hidden="true" />
        <div className="relative px-8 py-10 text-white">
          <p className="flex items-center gap-2 text-white/80">
            <Wallet className="w-5 h-5" aria-hidden="true" /> Current balance
          </p>
          <p className="text-6xl font-extrabold mt-2 flex items-center gap-3">
            <Coins className="w-8 h-8 text-amber-300" aria-hidden="true" />
            {walletQ.data ? formatPoints(walletQ.data.balance) : "—"}
            <span className="text-xl font-bold opacity-80">pts</span>
          </p>
          <div className="mt-5 flex gap-4 text-sm">
            <div className="flex items-center gap-1.5 rounded-xl bg-white/20 px-3 py-1.5">
              <ArrowUpRight className="w-4 h-4 text-emerald-300" aria-hidden="true" />
              <span className="font-semibold">{walletQ.data ? formatPoints(walletQ.data.lifetime_points_earned) : "—"}</span>
              <span className="opacity-80">earned</span>
            </div>
            <div className="flex items-center gap-1.5 rounded-xl bg-white/20 px-3 py-1.5">
              <ArrowDownRight className="w-4 h-4 text-red-300" aria-hidden="true" />
              <span className="font-semibold">{walletQ.data ? formatPoints(walletQ.data.lifetime_points_spent) : "—"}</span>
              <span className="opacity-80">spent</span>
            </div>
          </div>
        </div>
      </div>

      {/* Ledger */}
      <section aria-label="Transaction ledger">
        <Card variant="glass">
          <CardContent>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" aria-hidden="true" /> Transaction history
            </CardTitle>
            <CardDescription>Immutable ledger — every balance change is recorded.</CardDescription>
            {txQ.isLoading && <SkeletonTable rows={5} cols={4} />}
            {txQ.data && txQ.data.items.length === 0 && (
              <EmptyState icon={Coins} title="No transactions yet" description="Earn your first points by verifying a visit." />
            )}
            {txQ.data && txQ.data.items.length > 0 && (
              <div className="mt-4 space-y-2">
                {txQ.data.items.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-white/70 border border-white/40"
                  >
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                      tx.points >= 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                    }`}>
                      {tx.points >= 0 ? <ArrowUpRight className="w-4 h-4" aria-hidden="true" /> : <ArrowDownRight className="w-4 h-4" aria-hidden="true" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">
                        {tx.description || tx.transaction_type}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDate(tx.created_at)} {tx.reference ? `· ${tx.reference}` : ""}
                      </p>
                    </div>
                    <Badge variant={tx.points >= 0 ? "success" : "danger"}>
                      {tx.points >= 0 ? "+" : ""}{formatPoints(tx.points)} pts
                    </Badge>
                    {tx.balance_after != null && (
                      <Badge variant="default">balance {formatPoints(tx.balance_after)}</Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
