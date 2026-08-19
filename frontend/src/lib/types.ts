export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Obligation {
  tx_id: string;
  payer: string;
  payee: string;
  amount: string;
  currency: string;
  timestamp: string;
  status: "pending" | "netted" | "settled" | "failed";
  netting_window: number | null;
}

export interface NetPosition {
  participant: string;
  net_amount: string;
}

export interface SettlementAttempt {
  payer: string;
  payee: string;
  amount: string;
  status: "settled" | "failed";
}

export interface NettingWindow {
  window_id: number;
  start_time: string;
  end_time: string;
  gross_obligation_count: number;
  net_obligation_count: number;
  gross_volume: string;
  net_volume: string;
  liquidity_saved: string;
  created_at: string;
  net_positions: NetPosition[];
  settlement_attempts: SettlementAttempt[];
}

export interface Summary {
  total_windows: number;
  gross_obligation_count: number;
  net_obligation_count: number;
  gross_volume: string;
  net_volume: string;
  liquidity_saved: string;
  settled_attempts: number;
  failed_attempts: number;
}

export interface ParticipantBalance {
  participant: string;
  balance: string;
  last_updated: string;
}

export interface NettingPositionsResponse {
  window_id: number | null;
  start_time?: string;
  end_time?: string;
  positions: NetPosition[];
}