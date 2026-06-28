// src/pages/Dashboard.tsx
import React from "react";
import { useLatest, useSignals, useCycleStage, useTradeLogs } from "../hooks/useApi";
import { MetricCard } from "../components/MetricCard";
import { SignalCard } from "../components/SignalCard";
import { CyclePanel } from "../components/CyclePanel";
import { ReversalPanel } from "../components/ReversalPanel";
import { TradeLogPanel } from "../components/TradeLogPanel";
import { Skeleton } from "../components/ui/skeleton";

export default function Dashboard() {
  const { data: latest, isLoading: l1 } = useLatest();
  const { data: signals, isLoading: l2 } = useSignals();
  const { data: cycle, isLoading: l3 } = useCycleStage();
  const { data: logs, isLoading: l4 } = useTradeLogs(5);

  const isLoading = l1 || l2 || l3 || l4;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  // 格式化价格显示
  const formatPrice = (val: number | null | undefined, decimals: number = 2) => {
    if (val === null || val === undefined) return "--";
    return val.toFixed(decimals);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">猪周期量化监控大屏</h1>
          <p className="text-sm text-slate-400 mt-1">
            数据更新至：{latest?.date || "--"} | 策略G-终极版 | 夏普4.35
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-slate-400">实时连接</span>
        </div>
      </div>

      {/* 核心指标卡 - 6列网格（新增猪肉价格和仔猪价格） */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* 猪粮比 */}
        <MetricCard
          title="猪粮比"
          value={formatPrice(latest?.pig_grain_ratio)}
          change={0.5}
          unit=""
          trend="up"
        />
        {/* 猪肉价格 - 新增 */}
        <MetricCard
          title="猪肉价格"
          value={formatPrice(latest?.pig_price)}
          unit="元/kg"
        />
        {/* 仔猪价格 - 新增 */}
        <MetricCard
          title="仔猪价格"
          value={formatPrice(latest?.piglet_price)}
          unit="元/kg"
        />
        {/* 牧原收盘价 - 周末回退到上一交易日 */}
        <MetricCard
          title="牧原收盘价"
          value={formatPrice(latest?.muyuan_close)}
          change={-1.2}
          unit="元"
          trend="down"
          isFallback={latest?.muyuan_close_is_fallback}
          fallbackDate={latest?.muyuan_close_is_fallback ? latest?.date : undefined}
        />
        {/* 期货价 */}
        <MetricCard
          title="期货价(LH0)"
          value={formatPrice(latest?.futures_close, 0)}
          change={0.8}
          unit="元"
          trend="up"
        />
        {/* 畜牧指数 - 周末回退到上一交易日 */}
        <MetricCard
          title="畜牧指数"
          value={formatPrice(latest?.hog_index_close)}
          change={-0.5}
          unit="点"
          trend="down"
          isFallback={latest?.hog_index_close_is_fallback}
          fallbackDate={latest?.hog_index_close_is_fallback ? latest?.date : undefined}
        />
      </div>

      {/* 中部区域：信号状态 + 周期位置 + 反转面板 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <SignalCard data={signals} isLoading={false} />
        </div>
        <div className="space-y-4">
          <CyclePanel data={cycle} isLoading={l3} />
          <ReversalPanel 
            pgr={latest?.pig_grain_ratio}
            signals={signals}
          />
        </div>
      </div>

      {/* 推送记录 */}
      <TradeLogPanel data={logs || []} />
    </div>
  );
}
