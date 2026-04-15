import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DailyActivityRow } from '../types'

type Props = {
  data: DailyActivityRow[]
}

function shortDay(iso: string) {
  const d = new Date(iso + 'T12:00:00Z')
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function ConversationsChart({ data }: Props) {
  const chartData = data.map((row) => ({
    label: shortDay(row.day),
    new_conversations: row.new_conversations,
  }))

  return (
    <div className="chart-wrap chart-wrap--short">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="convGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            interval="preserveStartEnd"
            minTickGap={24}
          />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              background: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}
          />
          <Area
            type="monotone"
            dataKey="new_conversations"
            name="New conversations"
            stroke="var(--accent)"
            fill="url(#convGrad)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
