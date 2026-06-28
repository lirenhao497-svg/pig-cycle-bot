// 猪周期量化监控 - 通用工具函数

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** 合并 Tailwind 类名 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** 将日期字符串格式化为中文友好显示 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return '--'
  // 去掉尾部 00:00:00
  const clean = dateStr.slice(0, 10)
  return clean
}

/** 格式化数字：保留两位小数 + 千分位 */
export function formatPrice(v: number | null | undefined, decimals = 2): string {
  if (v == null || isNaN(v)) return '--'
  return v.toLocaleString('zh-CN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

/** 格式化百分比涨跌幅 */
export function formatChange(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return '--'
  const sign = v > 0 ? '+' : ''
  return `${sign}${v.toFixed(2)}%`
}

/** 涨跌颜色 */
export function changeColor(v: number | null | undefined): string {
  if (v == null) return 'text-slate-400'
  return v > 0 ? 'text-red-500' : v < 0 ? 'text-green-500' : 'text-slate-400'
}

/** 信号状态颜色 */
export function statusColor(status: string): string {
  switch (status) {
    case '清仓避险': return 'text-red-500'
    case '观望': return 'text-yellow-500'
    default: return 'text-green-500'
  }
}

/** 信号状态背景色 */
export function statusBgColor(status: string): string {
  switch (status) {
    case '清仓避险': return 'bg-red-500/10 border-red-500/30'
    case '观望': return 'bg-yellow-500/10 border-yellow-500/30'
    default: return 'bg-green-500/10 border-green-500/30'
  }
}

/** 信号状态脉冲动画 */
export function statusPulse(status: string): string {
  return status === '清仓避险' ? 'animate-signal-pulse' : ''
}

/** 周期阶段颜色 */
export function stageColor(stage: string): string {
  const map: Record<string, string> = {
    '深度亏损': 'text-red-600',
    '极端低位': 'text-orange-500',
    '偏弱': 'text-yellow-500',
    '中性': 'text-green-500',
    '高位': 'text-blue-500',
  }
  return map[stage] || 'text-slate-400'
}

/** 反转面板点数颜色 */
export function bullCountColor(count: number): string {
  if (count >= 3) return 'text-green-500'
  if (count >= 2) return 'text-yellow-500'
  return 'text-slate-500'
}
