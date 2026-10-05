import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { adminRewardsApi } from "@/api/rewards";
import { useToast } from "@/hooks/useToast";
import { Card, CardContent, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function AdminPage() {
  const { showToast } = useToast();
  
  const analyticsQ = useQuery({
    queryKey: ["admin", "rewards", "analytics"],
    queryFn: () => adminRewardsApi.analytics(),
  });

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-8">
      <header>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Admin Dashboard</h1>
      </header>
      <div className="grid gap-6">
        <Card>
          <CardContent>
            <CardTitle>Analytics</CardTitle>
            {analyticsQ.isLoading ? (
              <p>Loading analytics...</p>
            ) : analyticsQ.data ? (
              <pre>{JSON.stringify(analyticsQ.data, null, 2)}</pre>
            ) : (
              <p>No data</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
