import type { StickinessMetrics } from '../types'

const pct = new Intl.NumberFormat(undefined, { style: 'percent', maximumFractionDigits: 1 })
const nf = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 })
const ni = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 })

type Props = {
  s: StickinessMetrics
}

export function StickinessPanel({ s }: Props) {
  const median =
    s.median_days_between_active_days != null ? nf.format(s.median_days_between_active_days) : '—'

  return (
    <div className="kpi-grid">
      <article className="kpi-card">
        <h3 className="kpi-label">Distinct active users</h3>
        <p className="kpi-value">{ni.format(s.distinct_active_users)}</p>
        <p className="kpi-hint">Users with ≥1 inbound message in window</p>
      </article>
      <article className="kpi-card">
        <h3 className="kpi-label">Repeat visitors (2+ active days)</h3>
        <p className="kpi-value">{pct.format(s.repeat_visitor_share)}</p>
        <p className="kpi-hint">{ni.format(s.users_with_two_plus_active_days)} users on multiple days</p>
      </article>
      <article className="kpi-card">
        <h3 className="kpi-label">Avg. active days per user</h3>
        <p className="kpi-value">{nf.format(s.avg_distinct_active_days_per_user)}</p>
        <p className="kpi-hint">Distinct UTC days with inbound activity</p>
      </article>
      <article className="kpi-card">
        <h3 className="kpi-label">Median days between visits</h3>
        <p className="kpi-value">{median}</p>
        <p className="kpi-hint">Across consecutive active days (users with 2+ days)</p>
      </article>
      <article className="kpi-card">
        <h3 className="kpi-label">Half-period retention</h3>
        <p className="kpi-value">{pct.format(s.half_period_retention_rate)}</p>
        <p className="kpi-hint">Active in first half who return in second half</p>
      </article>
    </div>
  )
}
