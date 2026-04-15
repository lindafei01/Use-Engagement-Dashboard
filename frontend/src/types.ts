/** Mirrors backend Pydantic schemas (JSON uses ISO date/datetime strings). */

export interface HealthResponse {
  status: string
  database: string
}

export interface EngagementOverview {
  period_days: number
  total_inbound_messages: number
  total_outbound_messages: number
  total_conversations: number
  avg_daily_active_users: number
  avg_inbound_messages_per_active_user: number
  avg_messages_per_conversation: number
}

export interface DailyActivityRow {
  day: string
  inbound_messages: number
  outbound_messages: number
  active_users: number
  new_conversations: number
}

export interface TwinSummary {
  id: number
  name: string
  platform: string
  created_at: string
  user_count: number
  conversation_count: number
}

export interface QualityMetrics {
  period_days: number
  feedback_submissions: number
  feedback_positive: number
  feedback_negative: number
  helpfulness_rate: number
  outbound_messages_in_period: number
  share_of_outbound_with_feedback: number
  document_events_total: number
  document_events_by_type: Record<string, number>
  conversations_started: number
  outcome_completed_count: number
  outcome_abandoned_count: number
  outcome_open_count: number
  outcome_completed_share: number
}

export interface StickinessMetrics {
  period_days: number
  distinct_active_users: number
  users_with_two_plus_active_days: number
  repeat_visitor_share: number
  avg_distinct_active_days_per_user: number
  median_days_between_active_days: number | null
  half_period_retention_rate: number
}

export interface StructureBreakdownRow {
  key: string
  inbound_messages: number
  share: number
}

export interface StructureMetrics {
  period_days: number
  by_role: StructureBreakdownRow[]
  by_channel: StructureBreakdownRow[]
}
