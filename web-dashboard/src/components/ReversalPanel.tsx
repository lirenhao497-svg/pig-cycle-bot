// 反转面板组件
import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { SignalData } from "../types";

interface ReversalPanelProps {
  pgr?: number | null;
  signals?: SignalData | null;
}

export function ReversalPanel({ pgr, signals }: ReversalPanelProps) {
  // 简单反转条件判断
  const pgrLow = pgr != null && pgr < 5.0;
  const signalActive = signals?.status === "空仓" || signals?.status === "观望";
  const goldenCross = signals?.pgr_golden_cross || false;
  const aboveMa = signals?.muyuan_above_ma20 || false;

  const conditions = [
    { label: "猪粮比低位 (<5.0)", met: pgrLow },
    { label: "金叉信号", met: goldenCross },
    { label: "站上 MA20", met: aboveMa },
    { label: "信号安全", met: signalActive },
  ];

  const metCount = conditions.filter((c) => c.met).length;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700/50">
      <h3 className="text-sm text-slate-400 mb-4">反转面板</h3>
      <div className="text-3xl font-bold font-mono mb-2">
        <span className={metCount >= 3 ? "text-green-500" : metCount >= 2 ? "text-yellow-500" : "text-slate-500"}>
          {metCount}
        </span>
        <span className="text-base text-slate-500">/4</span>
      </div>
      <div className="space-y-2 mt-4">
        {conditions.map((c, i) => (
          <div key={i} className="flex items-center gap-2 text-sm">
            {c.met ? (
              <TrendingUp size={14} className="text-green-500 shrink-0" />
            ) : (
              <Minus size={14} className="text-slate-600 shrink-0" />
            )}
            <span className={c.met ? "text-slate-200" : "text-slate-500"}>{c.label}</span>
            <span className="ml-auto text-xs">{c.met ? "✓" : "✗"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
