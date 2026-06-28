// src/types/index.ts

// 最新市场数据（增加猪肉价格和仔猪价格）
export interface LatestData {
  date: string;
  pig_grain_ratio: number;
  muyuan_close: number | null;
  wenshi_close: number | null;
  futures_close: number | null;
  hog_index_close: number | null;
  // 新增：猪肉价格和仔猪价格
  pig_price: number | null;        // 猪肉价格（元/kg）
  piglet_price: number | null;     // 仔猪价格（元/kg）
  // 回退标记：周末/节假日时显示上一个交易日数据
  muyuan_close_is_fallback?: boolean;
  wenshi_close_is_fallback?: boolean;
  hog_index_close_is_fallback?: boolean;
}

// 信号状态
export interface SignalData {
  date: string;
  status: "空仓" | "清仓避险" | "观望";
  pgr_golden_cross: boolean;
  muyuan_above_ma20: boolean;
  muyuan_vol_contract: boolean;
  pig_grain_ratio: number;
  trigger_reason: string | null;
}

// 周期阶段
export interface CycleStage {
  date: string;
  pgr: number;
  stage: string;
  stage_label: string;
  label: string;
  bull_count?: number;
}

// 推送记录
export interface TradeLog {
  id: number;
  date: string;
  type: string;
  content: string;
  created_at: string;
  action?: string;
  advice?: string;
}

// 策略G交易记录
export interface SimPosition {
  id: number;
  open_date: string;
  close_date: string | null;
  symbol: string;
  open_price: number;
  close_price: number | null;
  pnl: number | null;
  hold_days: number | null;
  status: "open" | "closed";
}

// 模拟盘统计
export interface SimStats {
  total_trades: number;
  win_rate: number;
  avg_return: number;
  max_return: number;
  max_loss: number;
}

// 模拟盘数据
export interface SimulationData {
  current: SimPosition[];
  history: SimPosition[];
  stats: SimStats;
}

// L1观察记录
export interface L1WatchItem {
  date: string;
  pgr: number;
  consec: number;
  result: "potential_bottom" | "failed" | "pending";
}

// 图表数据点
export interface ChartDataPoint {
  date: string;
  pig_grain_ratio: number;
  muyuan_close: number;
  wenshi_close: number;
  futures_close: number;
  hog_index_close: number;
}

// 季节性数据
export interface SeasonalityData {
  month: number;
  avg_pgr: number;
  avg_muyuan: number;
}
