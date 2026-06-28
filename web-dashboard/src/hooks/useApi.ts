import { useQuery } from "@tanstack/react-query";

// 使用相对路径，通过 Vite proxy 转发到后端，避免 CORS
const API_BASE = "/api";

async function fetcher(url: string) {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API 错误 ${res.status}: ${text}`);
  }
  return res.json();
}

// 获取最新市场数据
export function useLatest() {
  return useQuery({
    queryKey: ["latest"],
    queryFn: () => fetcher(`${API_BASE}/latest`),
    refetchInterval: 60000,
  });
}

// 获取信号状态
export function useSignals() {
  return useQuery({
    queryKey: ["signals"],
    queryFn: () => fetcher(`${API_BASE}/signals`),
    refetchInterval: 60000,
  });
}

// 获取周期阶段
export function useCycleStage() {
  return useQuery({
    queryKey: ["cycle"],
    queryFn: () => fetcher(`${API_BASE}/cycle_stage`),
    refetchInterval: 60000,
  });
}

// 获取推送记录
export function useTradeLogs(limit: number = 5) {
  return useQuery({
    queryKey: ["tradeLogs", limit],
    queryFn: () => fetcher(`${API_BASE}/trade_log?limit=${limit}`),
    refetchInterval: 60000,
  });
}

// 获取策略G历史交易
export function useStrategyG() {
  return useQuery({
    queryKey: ["strategyG"],
    queryFn: () => fetcher(`${API_BASE}/strategy_g`),
  });
}

// 获取图表数据
export function useChartData(start?: string, end?: string) {
  const params = new URLSearchParams();
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  return useQuery({
    queryKey: ["chartData", start, end],
    queryFn: () => fetcher(`${API_BASE}/chart_data?${params.toString()}`),
  });
}

// 获取季节性数据
export function useSeasonality() {
  return useQuery({
    queryKey: ["seasonality"],
    queryFn: () => fetcher(`${API_BASE}/seasonality`),
  });
}

// 获取模拟盘数据
export function useSimulation() {
  return useQuery({
    queryKey: ["simulation"],
    queryFn: () => fetcher(`${API_BASE}/simulation`),
    refetchInterval: 60000,
  });
}

// 获取L1观察清单
export function useL1Watchlist() {
  return useQuery({
    queryKey: ["l1"],
    queryFn: () => fetcher(`${API_BASE}/l1_watchlist`),
    refetchInterval: 60000,
  });
}
