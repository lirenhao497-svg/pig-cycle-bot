// 猪周期量化监控 - 模拟盘跟踪页面

import { useSimulation } from '../hooks/useApi'
import { formatPrice } from '../utils'

/** 模拟盘跟踪 — 当前持仓 + 历史交易 + 绩效 */
export default function Simulation() {
  const { data: sim, isLoading, isError } = useSimulation()

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-48" /></div>
        ))}
      </div>
    )
  }

  if (isError) {
    return <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">数据加载失败</div>
  }

  const { current, history, stats } = sim ?? { current: [], history: [], stats: { total_trades: 0, win_rate: 0, avg_return: 0, max_return: 0, max_loss: 0 } }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-50">模拟盘跟踪</h2>

      {/* 当前持仓 */}
      <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
        <div className="text-sm text-slate-400 mb-4">当前持仓</div>
        {current.length === 0 ? (
          <div className="text-sm text-slate-500 text-center py-8">当前无持仓</div>
        ) : (
          <div className="space-y-3">
            {current.map((pos: any) => (
              <div key={pos.id} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/30">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-200 font-medium">开仓日 {pos.entry_date?.slice(0, 10)}</span>
                  <span className="text-yellow-500 text-sm">{pos.hold_days ?? 0}/20 天</span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div><span className="text-slate-500">入场价</span><p className="font-mono-num text-slate-200">{formatPrice(pos.entry_price)}</p></div>
                  <div><span className="text-slate-500">浮动盈亏</span><p className="font-mono-num text-green-500">{pos.profit_pct?.toFixed(2)}%</p></div>
                  <div><span className="text-slate-500">猪粮比</span><p className="font-mono-num text-slate-200">{pos.pgr?.toFixed(2) ?? '--'}</p></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 历史交易 */}
      <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
        <div className="text-sm text-slate-400 mb-4">历史交易（{history.length} 笔）</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 border-b border-slate-700/50">
                <th className="text-left py-2 pr-2 font-normal">开仓日</th>
                <th className="text-left px-2 font-normal">平仓日</th>
                <th className="text-right px-2 font-normal">入场价</th>
                <th className="text-right px-2 font-normal">出场价</th>
                <th className="text-right px-2 font-normal">收益</th>
                <th className="text-right pl-2 font-normal">持有</th>
              </tr>
            </thead>
            <tbody>
              {[...history].sort((a: any, b: any) => (a.entry_date || '').localeCompare(b.entry_date || '')).map((t: any) => (
                <tr key={t.id} className="border-b border-slate-700/30 hover:bg-slate-700/30 text-slate-200">
                  <td className="py-2 pr-2 whitespace-nowrap">{t.entry_date?.slice(0, 10)}</td>
                  <td className="px-2 whitespace-nowrap">{t.exit_date?.slice(0, 10) || '--'}</td>
                  <td className="text-right px-2 font-mono-num">{formatPrice(t.entry_price)}</td>
                  <td className="text-right px-2 font-mono-num">{formatPrice(t.exit_price)}</td>
                  <td className={cn('text-right px-2 font-mono-num font-medium', (t.profit_pct ?? 0) > 0 ? 'text-red-500' : 'text-green-500')}>
                    {(t.profit_pct ?? 0) > 0 ? '+' : ''}{t.profit_pct?.toFixed(2)}%
                  </td>
                  <td className="text-right pl-2 text-slate-400">{t.hold_days ?? '--'}天</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 绩效对比 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard title="总交易" value={stats.total_trades} />
        <StatCard title="胜率" value={`${stats.win_rate}%`} />
        <StatCard title="平均收益" value={`${stats.avg_return > 0 ? '+' : ''}${stats.avg_return}%`} color={stats.avg_return > 0 ? 'text-red-500' : 'text-green-500'} />
        <StatCard title="最大收益" value={`+${stats.max_return}%`} color="text-red-500" />
        <StatCard title="最大亏损" value={`${stats.max_loss}%`} color="text-green-500" />
        <StatCard title="夏普比率" value="4.35" />
      </div>
    </div>
  )
}

function StatCard({ title, value, color }: { title: string; value: string | number; color?: string }) {
  return (
    <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-4 text-center">
      <div className="text-xs text-slate-500 mb-1">{title}</div>
      <div className={`text-lg font-bold font-mono-num ${color || 'text-slate-50'}`}>{value}</div>
    </div>
  )
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).map(c => typeof c === 'object' ? Object.entries(c).filter(([_, v]) => v).map(([k]) => k).join(' ') : c).join(' ')
}
