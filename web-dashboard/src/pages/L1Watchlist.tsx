// 猪周期量化监控 - L1 观察清单页面

import { useL1Watchlist, useCycleStage } from '../hooks/useApi'
import { cn } from '../utils'

/** L1 观察清单 — 触发记录 + 90天判定 + 底部概率 */
export default function L1Watchlist() {
  const { data: watchlist = [], isLoading: lw, isError: ew } = useL1Watchlist()
  const { data: cycle } = useCycleStage()

  if (lw) {
    return (
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-48" /></div>
        ))}
      </div>
    )
  }

  if (ew) {
    return <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">数据加载失败</div>
  }

  const items = watchlist ?? []
  const currentPgr = cycle?.pgr ?? 4.01

  // 简单底部概率计算
  const isDeepLow = currentPgr < 4.0
  const isLow = currentPgr < 5.0
  const consec = (items.find(() => true) as any)?.consec ?? 0
  let prob = 0
  if (isDeepLow) prob += 40
  else if (isLow) prob += 15
  if (consec > 30) prob += 15
  if (consec > 60) prob += 10
  const bottomProb = Math.min(prob, 100)

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-50">L1 观察清单</h2>

      {/* 触发记录 */}
      <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
        <div className="text-sm text-slate-400 mb-4">触发记录</div>
        {items.length === 0 ? (
          <div className="text-sm text-slate-500 text-center py-12">
            <p className="mb-2">暂无触发记录</p>
            <p className="text-xs text-slate-600">当猪粮比跌破 4.0 且持续 30 天时将自动记录</p>
            <p className="text-xs text-slate-600 mt-1">当前猪粮比 {currentPgr.toFixed(2)}，距触发仍需 {Math.max(0, 4.0 - currentPgr).toFixed(2)}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 border-b border-slate-700/50">
                  <th className="text-left py-2 pr-2 font-normal">触发日期</th>
                  <th className="text-right px-2 font-normal">猪粮比</th>
                  <th className="text-right px-2 font-normal">连续天数</th>
                  <th className="text-left pl-2 font-normal">判定结果</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item: any) => (
                  <tr key={item.id} className="border-b border-slate-700/30 text-slate-200">
                    <td className="py-2 pr-2 whitespace-nowrap">{item.entry_date?.slice(0, 10)}</td>
                    <td className="text-right px-2 font-mono-num text-red-400">{item.pgr?.toFixed(2)}</td>
                    <td className="text-right px-2 font-mono-num">{item.consec}</td>
                    <td className="pl-2">
                      <span className={cn(
                        'text-xs px-2 py-0.5 rounded',
                        item.status === 'potential_bottom' ? 'bg-green-500/20 text-green-400' :
                        item.status === 'failed' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                      )}>
                        {item.status === 'potential_bottom' ? '底部确认' : item.status === 'failed' ? '失败' : '观察中'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 底部概率 */}
      <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
        <div className="text-sm text-slate-400 mb-4">底部概率评分</div>
        <div className="flex items-center justify-center flex-col gap-3">
          <div className="relative w-48 h-48">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="42" fill="none"
                stroke={bottomProb >= 70 ? '#22c55e' : bottomProb >= 40 ? '#eab308' : '#ef4444'}
                strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 42 * bottomProb / 100} ${2 * Math.PI * 42 * (100 - bottomProb) / 100}`}
                strokeLinecap="round"
                className="transition-all duration-1000"
              />
              <text x="50" y="48" textAnchor="middle" fill="#f8fafc" fontSize="18" fontWeight="bold" transform="rotate(90,50,50)">{bottomProb}%</text>
              <text x="50" y="62" textAnchor="middle" fill="#94a3b8" fontSize="10" transform="rotate(90,50,50)">底部概率</text>
            </svg>
          </div>
          <p className="text-sm text-slate-400">
            {bottomProb >= 70 ? '强底部信号，考虑中长期布局' : bottomProb >= 40 ? '初步底部信号，建议继续观察' : '未见底部迹象，保持空仓'}
          </p>
        </div>
      </div>
    </div>
  )
}
