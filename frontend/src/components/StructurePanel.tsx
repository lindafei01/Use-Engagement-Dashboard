import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { StructureMetrics } from '../types'

const pct = new Intl.NumberFormat(undefined, { style: 'percent', maximumFractionDigits: 1 })

type Props = {
  data: StructureMetrics
}

export function StructurePanel({ data }: Props) {
  const roleData = data.by_role.map((r) => ({
    ...r,
    label: r.key,
    shareLabel: pct.format(r.share),
  }))
  const channelData = data.by_channel.map((r) => ({
    ...r,
    label: r.key,
    shareLabel: pct.format(r.share),
  }))

  return (
    <div className="structure-pair">
      <div className="chart-wrap chart-wrap--structure">
        <p className="chart-caption">Inbound messages by role</p>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={roleData} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <YAxis
              type="category"
              dataKey="label"
              width={120}
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            />
            <Tooltip
              formatter={(v) => [Number(v ?? 0), 'Inbound']}
              labelFormatter={(l) => `${l} (${roleData.find((x) => x.label === l)?.shareLabel ?? ''})`}
              contentStyle={{
                background: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 8,
              }}
            />
            <Bar dataKey="inbound_messages" name="Inbound" fill="var(--chart-in)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-wrap chart-wrap--structure">
        <p className="chart-caption">Inbound messages by channel</p>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={channelData}
            layout="vertical"
            margin={{ left: 8, right: 24, top: 8, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
            <YAxis
              type="category"
              dataKey="label"
              width={140}
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            />
            <Tooltip
              formatter={(v) => [Number(v ?? 0), 'Inbound']}
              contentStyle={{
                background: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 8,
              }}
            />
            <Bar dataKey="inbound_messages" name="Inbound" fill="var(--chart-out)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
