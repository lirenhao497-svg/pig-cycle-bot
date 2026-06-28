// 猪周期量化监控 - Zustand 全局状态

import { create } from 'zustand'

/** 仪表盘全局状态 */
interface DashboardState {
  // 当前页面
  currentPath: string
  setCurrentPath: (path: string) => void

  // 数据更新时间
  lastUpdated: string | null
  setLastUpdated: (t: string) => void

  // 连接状态
  isConnected: boolean
  setConnected: (v: boolean) => void
}

export const useDashboardStore = create<DashboardState>((set) => ({
  currentPath: '/',
  setCurrentPath: (path) => set({ currentPath: path }),

  lastUpdated: null,
  setLastUpdated: (t) => set({ lastUpdated: t }),

  isConnected: false,
  setConnected: (v) => set({ isConnected: v }),
}))
