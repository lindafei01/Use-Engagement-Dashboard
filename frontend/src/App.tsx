import { useCallback, useEffect, useState } from 'react'
import {
  fetchDaily,
  fetchOverview,
  fetchQuality,
  fetchStickiness,
  fetchStructure,
  fetchTwins,
} from './api'
import { ConversationsChart } from './components/ConversationsChart'
import { DailyActivityChart } from './components/DailyActivityChart'
import { KpiCards } from './components/KpiCards'
import { QualityPanel } from './components/QualityPanel'
import { StickinessPanel } from './components/StickinessPanel'
import { StructurePanel } from './components/StructurePanel'
import { TwinsTable } from './components/TwinsTable'
import type {
  DailyActivityRow,
  EngagementOverview,
  QualityMetrics,
  StickinessMetrics,
  StructureMetrics,
  TwinSummary,
} from './types'

const PERIOD_OPTIONS = [7, 30, 90] as const

export default function App() {
  const [days, setDays] = useState<number>(30)
  const [overview, setOverview] = useState<EngagementOverview | null>(null)
  const [daily, setDaily] = useState<DailyActivityRow[]>([])
  const [quality, setQuality] = useState<QualityMetrics | null>(null)
  const [stickiness, setStickiness] = useState<StickinessMetrics | null>(null)
  const [structure, setStructure] = useState<StructureMetrics | null>(null)
  const [twins, setTwins] = useState<TwinSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [ov, d, qu, st, str, t] = await Promise.all([
        fetchOverview(days),
        fetchDaily(days),
        fetchQuality(days),
        fetchStickiness(days),
        fetchStructure(days),
        fetchTwins(),
      ])
      setOverview(ov)
      setDaily(d)
      setQuality(qu)
      setStickiness(st)
      setStructure(str)
      setTwins(t)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="dashboard">
      <header className="dash-header">
        <div className="dash-title">
          <h1>Twin engagement</h1>
          <p className="dash-subtitle">
            Volume, quality, stickiness, and workspace structure — how much the product is used, whether
            it delivers value, and how adoption spreads across roles and channels.
          </p>
        </div>
        <div className="dash-toolbar">
          <label className="period-label" htmlFor="period">
            Window
          </label>
          <select
            id="period"
            className="period-select"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            {PERIOD_OPTIONS.map((d) => (
              <option key={d} value={d}>
                Last {d} days
              </option>
            ))}
          </select>
          <button type="button" className="btn-refresh" onClick={() => void load()} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => void load()}>
            Retry
          </button>
        </div>
      )}

      {loading && !overview ? (
        <p className="loading">Loading…</p>
      ) : overview && quality && stickiness && structure ? (
        <>
          <section className="section">
            <h2 className="section-title">Volume — messages &amp; sessions</h2>
            <p className="section-desc">
              Activity level in the last {overview.period_days} UTC calendar days: throughput and depth per
              conversation.
            </p>
            <KpiCards overview={overview} />
          </section>

          <section className="section">
            <h2 className="section-title">Volume — daily trend</h2>
            <p className="section-desc">Inbound and outbound messages; bars show daily active users.</p>
            <DailyActivityChart data={daily} />
          </section>

          <section className="section">
            <h2 className="section-title">Volume — new conversations</h2>
            <p className="section-desc">New threads started per day.</p>
            <ConversationsChart data={daily} />
          </section>

          <section className="section">
            <h2 className="section-title">Quality — feedback, outcomes, documents</h2>
            <p className="section-desc">
              Whether replies are rated helpful, sessions reach a &quot;completed&quot; outcome, and users
              generate drafts in their style (email, memo, etc.).
            </p>
            <QualityPanel q={quality} />
          </section>

          <section className="section">
            <h2 className="section-title">Stickiness — retention &amp; return cadence</h2>
            <p className="section-desc">
              Repeat usage within the window, median gap between active days, and overlap between the first
              and second half of the period.
            </p>
            <StickinessPanel s={stickiness} />
          </section>

          <section className="section">
            <h2 className="section-title">Structure — owners vs collaborators &amp; channels</h2>
            <p className="section-desc">
              Where inbound traffic comes from: Twin owner vs colleagues, and Slack / DM / channel
              distribution.
            </p>
            <StructurePanel data={structure} />
          </section>

          <section className="section">
            <h2 className="section-title">Twins</h2>
            <p className="section-desc">Deployed instances and cumulative reach.</p>
            <TwinsTable twins={twins} />
          </section>
        </>
      ) : null}

      <footer className="dash-footer">
        <span>Twin Engagement Dashboard</span>
        <a href="/docs" target="_blank" rel="noreferrer">
          API docs (Swagger)
        </a>
      </footer>
    </div>
  )
}
