import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { useEffect } from "react";
import { useState } from "react";
import { ApiError } from "@/api/client";
import { walletApi } from "@/api/rewards";
import { useAuth } from "./useAuth";

/** Hook for authenticated data queries with common defaults. */
export function useAuthQuery<T>(
  key: readonly unknown[],
  fn: () => Promise<T>,
  options?: Omit<UseQueryOptions<T, ApiError>, "queryKey" | "queryFn">
) {
  const { user } = useAuth();
  return useQuery<T, ApiError>({
    queryKey: key,
    queryFn: fn,
    enabled: !!user,
    ...options,
  });
}

export function useWallet() {
  return useAuthQuery(["wallet"], () => walletApi.get());
}

export function useInvalidatingMutation<TData, TVariables>(
  fn: (vars: TVariables) => Promise<TData>,
  invalidate: readonly unknown[][] = []
) {
  const qc = useQueryClient();
  return useMutation<TData, ApiError, TVariables>({
    mutationFn: fn,
    onSuccess: () => {
      for (const key of invalidate) {
        qc.invalidateQueries({ queryKey: key });
      }
    },
  });
}

/** Debounce a string/value for search inputs. */
export function useDebounced<T>(value: T, delay = 400): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return v;
}
