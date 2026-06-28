// src/components/MetricCard.tsx
import React from "react";
import { TrendingUp, TrendingDown, Clock } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  unit?: string;
  trend?: "up" | "down";
  isFallback?: boolean;  // 是否为回退数据（上一个交易日）
  fallbackDate?: string; // 回退数据的日期
}

export function MetricCard({ 
  title, 
  value, 
  change, 
  unit, 
  trend, 
  isFallback,
  fallbackDate 
}: MetricCardProps) {
  const isUp = trend === "up";
  const colorClass = isUp ? "text-red-500" : "text-green-500";
  const bgClass = isUp ? "bg-red-500/10" : "bg-green-500/10";
  const Icon = isUp ? TrendingUp : TrendingDown;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700/50 hover:border-slate-600 transition-all relative">
      {/* 回退标记：周末/节假日时显示"上一交易日" */}
      {isFallback && (
        <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/10 border border-yellow-500/20">
          <Clock className="w-3 h-3 text-yellow-500" />
          <span className="text-xs text-yellow-500">
            {fallbackDate ? `${fallbackDate}收盘` : "上一交易日"}
          </span>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        {trend && (
          <div className={`p-2 rounded-lg ${bgClass}`}>
            <Icon className={`w-4 h-4 ${colorClass}`} />
          </div>
        )}
      </div>

      <div className="mt-4">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-slate-50 font-mono">{value}</span>
          {unit && <span className="text-sm text-slate-500">{unit}</span>}
        </div>

        {change !== undefined && (
          <div className={`mt-2 text-sm font-medium ${colorClass}`}>
            {isUp ? "+" : ""}{change.toFixed(2)}%
          </div>
        )}
      </div>
    </div>
  );
}
