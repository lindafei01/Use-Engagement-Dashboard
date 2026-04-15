import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { QualityMetrics } from '../types'

const pct = new Intl.NumberFormat(undefined, { style: 'percent', maximumFractionDigits: 1 })
const ni = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 })

type Props = {
  q: QualityMetrics
}

export function QualityPanel({ q }: Props) {
  const docData = Object.entries(q.document_events_by_type).map(([name, value]) => ({
    name: name.replace(/^#/, ''),
    value,
  }))

  return (
    <div className="quality-panel">
      <div className="kpi-grid">
        <article className="kpi-card">
          <h3 className="kpi-label">Feedback submissions</h3>
          <p className="kpi-value">{ni.format(q.feedback_submissions)}</p>
          <p className="kpi-hint">
            Positive {ni.format(q.feedback_positive)} · Negative {ni.format(q.feedback_negative)}
          </p>
        </article>
        <article className="kpi-card">
          <h3 className="kpi-label">Helpfulness rate</h3>
          <p className="kpi-value">{pct.format(q.helpfulness_rate)}</p>
          <p className="kpi-hint">Share of thumbs-up among ratings</p>
        </article>
        <article className="kpi-card">
          <h3 className="kpi-label">Outbound with feedback</h3>
          <p className="kpi-value">{pct.format(q.share_of_outbound_with_feedback)}</p>
          <p className="kpi-hint">Coverage of explicit ratings on Twin replies</p>
        </article>
        <article className="kpi-card">
          <h3 className="kpi-label">Document drafts</h3>
          <p className="kpi-value">{ni.format(q.document_events_total)}</p>
          <p className="kpi-hint">Emails, memos, Slack posts in user style</p>
        </article>
        <article className="kpi-card">
          <h3 className="kpi-label">Sessions marked completed</h3>
          <p className="kpi-value">{pct.format(q.outcome_completed_share)}</p>
          <p className="kpi-hint">
            Completed {ni.format(q.outcome_completed_count)} · Abandoned {ni.format(q.outcome_abandoned_count)}{' '}
            · Open {ni.format(q.outcome_open_count)}
          </p>
        </article>
      </div>
      {docData.length > 0 && (
        <div className="chart-wrap chart-wrap--short" style={{ marginTop: '1rem' }}>
          <p className="chart-caption">Document events by type</p>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={docData} layout="vertical" margin={{ left: 16, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
              <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={100}
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="value" name="Events" fill="var(--accent)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
