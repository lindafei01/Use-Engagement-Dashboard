import type {
  DailyActivityRow,
  EngagementOverview,
  HealthResponse,
  QualityMetrics,
  StickinessMetrics,
  StructureMetrics,
  TwinSummary,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function getJson<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function fetchHealth(): Promise<HealthResponse> {
  return getJson('/api/health')
}

export function fetchOverview(days: number): Promise<EngagementOverview> {
  const q = new URLSearchParams({ days: String(days) })
  return getJson(`/api/metrics/overview?${q}`)
}

export function fetchDaily(days: number): Promise<DailyActivityRow[]> {
  const q = new URLSearchParams({ days: String(days) })
  return getJson(`/api/metrics/daily?${q}`)
}

export function fetchQuality(days: number): Promise<QualityMetrics> {
  const q = new URLSearchParams({ days: String(days) })
  return getJson(`/api/metrics/quality?${q}`)
}

export function fetchStickiness(days: number): Promise<StickinessMetrics> {
  const q = new URLSearchParams({ days: String(days) })
  return getJson(`/api/metrics/stickiness?${q}`)
}

export function fetchStructure(days: number): Promise<StructureMetrics> {
  const q = new URLSearchParams({ days: String(days) })
  return getJson(`/api/metrics/structure?${q}`)
}

export function fetchTwins(): Promise<TwinSummary[]> {
  return getJson('/api/twins')
}
