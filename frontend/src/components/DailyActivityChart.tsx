import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  Bar,
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

export function DailyActivityChart({ data }: Props) {
  const chartData = data.map((row) => ({
    ...row,
    label: shortDay(row.day),
  }))

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            interval="preserveStartEnd"
            minTickGap={24}
          />
          <YAxis yAxisId="left" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}
            labelStyle={{ color: 'var(--text)' }}
          />
          <Legend />
          <Bar
            yAxisId="right"
            dataKey="active_users"
            name="Active users"
            fill="var(--chart-bar)"
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="inbound_messages"
            name="Inbound"
            stroke="var(--chart-in)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="outbound_messages"
            name="Outbound"
            stroke="var(--chart-out)"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
