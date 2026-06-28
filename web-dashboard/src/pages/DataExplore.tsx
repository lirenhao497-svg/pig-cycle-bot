// 猪周期量化监控 - 数据探索页面

import ReactEChartsCore from 'echarts-for-react'
import { useChartData, useSeasonality } from '../hooks/useApi'

/** 数据探索页面 — 多轴图 + 季节性 + 数据导出 */
export default function DataExplore() {
  const { data: chartData, isLoading: lc, isError: ec } = useChartData()
  const { data: season, isLoading: ls } = useSeasonality()

  if (lc || ls) {
    return (
      <div className="space-y-4">
        <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-96" /></div>
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-64" /></div>
          <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6"><div className="skeleton h-64" /></div>
        </div>
      </div>
    )
  }

  if (ec) {
    return <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">数据加载失败</div>
  }

  const data = chartData ?? []
  const dates = data.map((d: any) => d.date?.slice(0, 7))
  const pgrValues = data.map((d: any) => d.pig_grain_ratio ?? null)
  const muyuanValues = data.map((d: any) => d.muyuan_close ?? null)
  const futuresValues = data.map((d: any) => (d.futures_close ?? null) ? (d.futures_close ?? 0) / 1000 : null)

  // 多轴图
  const multiAxisOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const, axisPointer: { type: 'cross' as const } },
    legend: { data: ['猪粮比', '牧原', '期货(千元)'], textStyle: { color: '#94a3b8' }, top: 0 },
    grid: { left: 60, right: 60, top: 40, bottom: 40 },
    dataZoom: [{ type: 'inside' as const }, { type: 'slider' as const }],
    xAxis: { type: 'category' as const, data: dates, axisLabel: { color: '#94a3b8', fontSize: 10, interval: 11 } },
    yAxis: [
      { type: 'value' as const, name: '猪粮比', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      { type: 'value' as const, name: '价格', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { show: false } },
    ],
    series: [
      { name: '猪粮比', type: 'line', data: pgrValues, smooth: true, lineStyle: { color: '#3b82f6', width: 1.5 }, symbol: 'none', yAxisIndex: 0 },
      { name: '牧原', type: 'line', data: muyuanValues, smooth: true, lineStyle: { color: '#ef4444', width: 1.5 }, symbol: 'none', yAxisIndex: 1 },
      { name: '期货(千元)', type: 'line', data: futuresValues, smooth: true, lineStyle: { color: '#eab308', width: 1.5 }, symbol: 'none', yAxisIndex: 1 },
    ],
  }

  // 季节性柱状图
  const { months, avg_pgr, avg_muyuan } = season ?? { months: [], avg_pgr: [], avg_muyuan: [] }
  const seasonOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['猪粮比均值', '牧原均值'], textStyle: { color: '#94a3b8' } },
    grid: { left: 50, right: 30, top: 40, bottom: 30 },
    xAxis: { type: 'category' as const, data: (months || []).map((m: number) => `${m}月`), axisLabel: { color: '#94a3b8' } },
    yAxis: [
      { type: 'value' as const, name: '猪粮比', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      { type: 'value' as const, name: '牧原价', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { show: false } },
    ],
    series: [
      { name: '猪粮比均值', type: 'bar', data: avg_pgr, itemStyle: { color: '#3b82f6' }, yAxisIndex: 0 },
      { name: '牧原均值', type: 'line', data: avg_muyuan, lineStyle: { color: '#ef4444' }, symbol: 'circle', symbolSize: 6, yAxisIndex: 1 },
    ],
  }

  // CSV 导出
  const handleExportCsv = () => {
    if (data.length === 0) return
    const header = 'date,pig_grain_ratio,muyuan_close,wenshi_close,futures_close,hog_index_close'
    const rows = data.map((d: any) => `${d.date},${d.pig_grain_ratio ?? ''},${d.muyuan_close ?? ''},${d.wenshi_close ?? ''},${d.futures_close ?? ''},${d.hog_index_close ?? ''}`)
    const csv = [header, ...rows].join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pig_cycle_data_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-50">数据探索</h2>

      {/* 多轴图 */}
      <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
        <div className="text-sm text-slate-400 mb-2">时间序列多轴图（猪粮比 / 牧原 / 期货）</div>
        <ReactEChartsCore option={multiAxisOption} style={{ height: 420 }} notMerge />
      </div>

      {/* 季节性 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6">
          <div className="text-sm text-slate-400 mb-4">季节性 - 各月均值</div>
          <ReactEChartsCore option={seasonOption} style={{ height: 280 }} notMerge />
        </div>

        {/* 数据导出 */}
        <div className="rounded-xl bg-slate-800 border border-slate-700/50 p-6 flex flex-col justify-center items-center gap-4">
          <div className="text-sm text-slate-400">数据导出</div>
          <p className="text-xs text-slate-500 text-center max-w-xs">导出 market_daily 全部数据为 CSV 文件，包含猪粮比、牧原、温氏、期货、畜牧指数</p>
          <button
            onClick={handleExportCsv}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
          >
            导出 CSV
          </button>
        </div>
      </div>
    </div>
  )
}
