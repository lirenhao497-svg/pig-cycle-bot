// 猪周期量化监控 - 信号状态卡片（中左侧）

import { CheckCircle2, AlertTriangle, Info, TrendingUp, BarChart3, Activity } from 'lucide-react'
import { cn, statusColor, statusBgColor, statusPulse } from '../utils'
import type { SignalData } from '../types'

interface SignalCardProps {
  data?: SignalData
  isLoading: boolean
}

/** 信号状态大卡片：显示当前空仓/清仓避险/观望 + 3 条件检查 */
export function SignalCard({ data, isLoading }: SignalCardProps) {
  if (isLoading) {
    return <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-48" /></div>
  }
  if (!data) {
    return <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6 flex items-center justify-center text-slate-500">暂无信号数据</div>
  }

  const { status, trigger_reason, pgr_golden_cross, muyuan_above_ma20, muyuan_vol_contract, pig_grain_ratio } = data
  const configs = [
    { label: '猪粮比金叉 (5日上穿20日)', ok: pgr_golden_cross, icon: TrendingUp },
    { label: '牧原站上 20 日均线', ok: muyuan_above_ma20, icon: BarChart3 },
    { label: '波动率收缩', ok: muyuan_vol_contract, icon: Activity },
  ]

  const StatusIcon = status === '清仓避险' ? AlertTriangle : status === '观望' ? Info : CheckCircle2

  return (
    <div className={cn('rounded-xl border p-6 transition-all duration-200', statusBgColor(status), statusPulse(status))}>
      {/* 状态标题 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <StatusIcon size={24} className={statusColor(status)} />
          <span className={cn('text-xl font-bold', statusColor(status))}>{status}</span>
        </div>
        <span className="text-sm text-slate-500 bg-slate-800/50 px-2 py-0.5 rounded font-mono-num">pgr {pig_grain_ratio?.toFixed(2)}</span>
      </div>

      {/* 触发原因 */}
      {trigger_reason && (
        <div className="text-sm text-slate-300 bg-slate-900/50 rounded-lg px-3 py-2 mb-4">{trigger_reason}</div>
      )}
      {status === '空仓' && (
        <div className="text-sm text-slate-400 mb-4">正常持仓，无风险信号</div>
      )}

      {/* 3 条件状态 */}
      <div className="space-y-3">
        {configs.map((cfg) => (
          <div key={cfg.label} className="flex items-center gap-2 text-sm">
            <div className={cn('w-2 h-2 rounded-full shrink-0', cfg.ok ? 'bg-green-500' : 'bg-slate-600')} />
            <cfg.icon size={14} className="text-slate-400 shrink-0" />
            <span className={cn(cfg.ok ? 'text-slate-200' : 'text-slate-500')}>{cfg.label}</span>
            <span className="ml-auto text-xs font-mono-num">{cfg.ok ? '✓' : '✗'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
