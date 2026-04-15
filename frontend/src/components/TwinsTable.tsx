import type { TwinSummary } from '../types'

type Props = {
  twins: TwinSummary[]
}

const df = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function platformBadgeClass(platform: string): string {
  const p = platform.toLowerCase()
  if (p === 'slack') return 'platform-badge--slack'
  if (p === 'web') return 'platform-badge--web'
  return 'platform-badge--other'
}

export function TwinsTable({ twins }: Props) {
  if (twins.length === 0) {
    return <p className="empty-hint">No Twins found. Run the seed script on the backend.</p>
  }

  return (
    <div className="table-scroll">
      <table className="twins-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Platform</th>
            <th>Users</th>
            <th>Conversations</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {twins.map((t) => (
            <tr key={t.id}>
              <td className="cell-name">{t.name}</td>
              <td>
                <span className={`platform-badge ${platformBadgeClass(t.platform)}`}>{t.platform}</span>
              </td>
              <td>{t.user_count}</td>
              <td>{t.conversation_count}</td>
              <td className="cell-muted">{df.format(new Date(t.created_at))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
