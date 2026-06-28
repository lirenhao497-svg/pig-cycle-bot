// 猪周期量化监控 - 策略回测可视化页面

import ReactEChartsCore from 'echarts-for-react'
import { useStrategyG, useChartData } from '../hooks/useApi'
import { formatPrice } from '../utils'

/** 策略回测页面 — 收益曲线 + 月度分布 + 交易明细 + 热力图 */
export default function Backtest() {
  const { data: trades, isLoading: lt, isError: et } = useStrategyG()
  const { data: chartData, isLoading: lc } = useChartData()

  if (lt || lc) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
            <div className="skeleton h-72" />
          </div>
        ))}
      </div>
    )
  }

  if (et) {
    return <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">数据加载失败</div>
  }

  const tradeList: any[] = trades ?? []

  // 累计收益曲线
  const cumReturns = tradeList
    .filter((t: any) => t.profit_pct != null)
    .reduce<{ labels: string[]; values: number[]; points: { x: number; y: number; label: string }[] }>(
      (acc: any, t: any, i: number) => {
        const prev = i > 0 ? acc.values[i - 1] : 0
        acc.labels.push(t.entry_date?.slice(0, 7) || '')
        acc.values.push(+(prev + t.profit_pct).toFixed(2))
        acc.points.push({ x: i, y: +(prev + t.profit_pct).toFixed(2), label: `+${t.profit_pct}%` })
        return acc
      },
      { labels: [], values: [], points: [] },
    )

  const cumOption = {
    backgroundColor: 'transparent',
    grid: { left: 60, right: 30, top: 30, bottom: 40 },
    tooltip: { trigger: 'axis' as const },
    xAxis: { type: 'category' as const, data: cumReturns.labels, axisLabel: { color: '#94a3b8', fontSize: 11 } },
    yAxis: { type: 'value' as const, name: '累计收益 %', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
    series: [
      { name: '策略G累计', type: 'line', data: cumReturns.values, smooth: true, lineStyle: { color: '#ef4444', width: 2 }, areaStyle: { color: 'rgba(239,68,68,0.1)' }, symbol: 'circle', symbolSize: 8, itemStyle: { color: '#ef4444' } },
      { name: '交易点', type: 'scatter', data: cumReturns.points.map((p) => [p.x, p.y]), symbolSize: 12, itemStyle: { color: '#eab308' } },
    ],
  }

  // 月度分布柱状图
  const monthData = Array.from({ length: 12 }, (_, i) => {
    const mths = tradeList.filter((t: any) => {
      const m = t.entry_date ? parseInt(t.entry_date.slice(5, 7)) : 0
      return m === i + 1
    })
    const n = mths.length
    const wr = n > 0 ? (mths.filter((t: any) => t.profit_pct > 0).length / n * 100) : 0
    const avg = n > 0 ? mths.reduce((s: number, t: any) => s + t.profit_pct, 0) / n : 0
    return { month: `${i + 1}月`, count: n, winRate: +wr.toFixed(1), avgReturn: +avg.toFixed(2) }
  })

  const monthOption = {
    backgroundColor: 'transparent',
    grid: { left: 50, right: 50, top: 30, bottom: 30 },
    tooltip: { trigger: 'axis' as const },
    xAxis: { type: 'category' as const, data: monthData.map((m) => m.month), axisLabel: { color: '#94a3b8' } },
    yAxis: [
      { type: 'value' as const, name: '次数', axisLabel: { color: '#94a3b8' }, splitLine: { show: false } },
      { type: 'value' as const, name: '胜率 %', axisLabel: { color: '#94a3b8' }, splitLine: { show: false } },
    ],
    series: [
      { name: '交易次数', type: 'bar', data: monthData.map((m) => m.count), itemStyle: { color: '#3b82f6' }, barWidth: 20 },
      { name: '胜率', type: 'line', yAxisIndex: 1, data: monthData.map((m) => m.winRate), lineStyle: { color: '#eab308' }, symbol: 'circle', symbolSize: 6 },
    ],
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-50">策略回测可视化</h2>

      {/* 收益曲线 */}
      <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
        <div className="text-sm text-slate-400 mb-4">策略G累计收益 vs 买入持有</div>
        <ReactEChartsCore option={cumOption} style={{ height: 320 }} notMerge />
      </div>

      {/* 月度分布 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
          <div className="text-sm text-slate-400 mb-4">月度分布</div>
          <ReactEChartsCore option={monthOption} style={{ height: 280 }} notMerge />
        </div>

        {/* 交易明细表格 */}
        <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
          <div className="text-sm text-slate-400 mb-4">交易明细（{tradeList.length} 笔）</div>
          <div className="overflow-x-auto max-h-72 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 border-b border-slate-700/50">
                  <th className="text-left py-2 pr-2 font-normal">日期</th>
                  <th className="text-right px-2 font-normal">开仓</th>
                  <th className="text-right px-2 font-normal">平仓</th>
                  <th className="text-right px-2 font-normal">收益</th>
                  <th className="text-right pl-2 font-normal">持有</th>
                </tr>
              </thead>
              <tbody>
                {[...tradeList].sort((a: any, b: any) => (a.entry_date || '').localeCompare(b.entry_date || '')).map((t: any) => (
                  <tr key={t.id} className="border-b border-slate-700/30 hover:bg-slate-700/30 text-slate-200">
                    <td className="py-2 pr-2 whitespace-nowrap">{t.entry_date?.slice(0, 10)}</td>
                    <td className="text-right px-2 font-mono-num">{formatPrice(t.entry_price)}</td>
                    <td className="text-right px-2 font-mono-num">{formatPrice(t.exit_price)}</td>
                    <td className={cn('text-right px-2 font-mono-num font-medium', (t.profit_pct ?? 0) > 0 ? 'text-red-500' : 'text-green-500')}>
                      {(t.profit_pct ?? 0) > 0 ? '+' : ''}{t.profit_pct?.toFixed(2)}%
                    </td>
                    <td className="text-right pl-2 text-slate-400">{t.hold_days ?? (t.exit_date && t.entry_date ? Math.round((new Date(t.exit_date).getTime() - new Date(t.entry_date).getTime()) / 86400000) : '--')}天</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).map(c => typeof c === 'object' ? Object.entries(c).filter(([_, v]) => v).map(([k]) => k).join(' ') : c).join(' ')
}
