// 猪周期量化监控 - 推送记录表

import { AlertTriangle, Bell, Info, Clock } from 'lucide-react'
import { formatDate } from '../utils'
import type { TradeLog as TradeLogItem } from '../types'

interface TradeLogPanelProps {
  data?: TradeLogItem[]
  isLoading?: boolean
}

/** 底部推送记录 */
export function TradeLogPanel({ data, isLoading }: TradeLogPanelProps) {
  if (isLoading) {
    return <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-32" /></div>
  }

  const items = data ?? []

  return (
    <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-slate-400">最近推送记录</div>
        <Clock size={14} className="text-slate-500" />
      </div>

      {items.length === 0 ? (
        <div className="text-sm text-slate-500 text-center py-6">暂无推送记录</div>
      ) : (
        <div className="space-y-2">
          {items.map((log) => {
            const isClear = log.action === 'clear' || log.action === 'short'
            const isWait = log.action === 'wait' || log.action === '观望'
            const Icon = isClear ? AlertTriangle : isWait ? Info : Bell
            const iconColor = isClear ? 'text-red-500' : isWait ? 'text-green-500' : 'text-yellow-500'
            return (
              <div key={log.id} className="flex items-start gap-3 py-2 border-b border-slate-700/30 last:border-0">
                <Icon size={16} className={`shrink-0 mt-0.5 ${iconColor}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-slate-400 font-mono-num">{log.date?.slice(0, 10)}</div>
                  <div className="text-sm text-slate-200 truncate">{log.advice?.slice(0, 60)}</div>
                </div>
                <span className={cn('text-xs px-1.5 py-0.5 rounded shrink-0', isClear ? 'bg-red-500/20 text-red-400' : isWait ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400')}>
                  {isClear ? '清仓' : isWait ? '空仓' : '观望'}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).map(c => {
    if (typeof c === 'object') return Object.entries(c).filter(([_, v]) => v).map(([k]) => k).join(' ')
    return c
  }).join(' ')
}
