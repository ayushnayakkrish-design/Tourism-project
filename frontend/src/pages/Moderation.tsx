import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  ShieldCheck, CheckCircle2, XCircle, Users, MessageSquare,
  ClipboardList, RefreshCw,
} from "lucide-react";
import { moderationApi } from "@/api/community";
import { useToast } from "@/hooks/useToast";
import { errorMessage } from "@/api/client";
import { Card, CardContent, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SkeletonTable } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { formatDate } from "@/lib/utils";

export function ModerationPage() {
  const { showToast } = useToast();
  const [rejectTarget, setRejectTarget] = useState<{ type: string; id: string } | null>(null);
  const [reason, setReason] = useState("");
  const [tab, setTab] = useState<"queue" | "history">("queue");

  const queueQ = useQuery({
    queryKey: ["moderation", "queue"],
    queryFn: () => moderationApi.queue(),
  });

  const historyQ = useQuery({
    queryKey: ["moderation", "history"],
    queryFn: () => moderationApi.history({ page: 1, page_size: 20 }),
    enabled: tab === "history",
  });

  const approveMutation = useMutation({
    mutationFn: async ({ type, id }: { type: string; id: string }) =>
      type === "submission" ? await moderationApi.approveSubmission(id) : await moderationApi.approveReview(id),
    onSuccess: () => {
      showToast({ type: "success", title: "Approved" });
      queueQ.refetch();
    },
    onError: (err: any) => showToast({ type: "error", title: "Approve failed", message: errorMessage(err) }),
  });

  const rejectMutation = useMutation({
    mutationFn: async () => {
      if (!rejectTarget) throw new Error("No target");
      return rejectTarget.type === "submission"
        ? await moderationApi.rejectSubmission(rejectTarget.id, reason.trim() || "Does not meet guidelines")
        : await moderationApi.rejectReview(rejectTarget.id, reason.trim() || "Does not meet guidelines");
    },
    onSuccess: () => {
      showToast({ type: "success", title: "Rejected", message: "Moderator note recorded." });
      setRejectTarget(null);
      setReason("");
      queueQ.refetch();
    },
    onError: (err: any) => showToast({ type: "error", title: "Reject failed", message: errorMessage(err) }),
  });

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-8 h-8" aria-hidden="true" /> Moderation
        </h1>
        <p className="mt-1 text-slate-600">
          GET /api/moderation/queue · POST /api/moderation/submissions/:id/approve|reject
        </p>
      </header>
    </div>
  );
}