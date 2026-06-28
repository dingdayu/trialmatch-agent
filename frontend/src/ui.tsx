import type { ReactNode } from "react"

export function PageHeader({
  kicker,
  title,
  description,
  actions,
}: {
  readonly kicker: string
  readonly title: string
  readonly description: string
  readonly actions?: ReactNode
}) {
  return (
    <section className="page-header">
      <div>
        <span className="eyebrow">{kicker}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions === undefined ? null : <div className="page-actions">{actions}</div>}
    </section>
  )
}

export function MetricCard({
  label,
  value,
  tone = "default",
}: {
  readonly label: string
  readonly value: string | number
  readonly tone?: "default" | "success" | "warning" | "danger" | "info"
}) {
  return (
    <div className={`metric-card metric-${tone}`}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  )
}

export function DataCard({ children }: { readonly children: ReactNode }) {
  return <section className="data-card">{children}</section>
}

export function CardTitle({ title, meta, actions }: { readonly title: string; readonly meta?: string; readonly actions?: ReactNode }) {
  return (
    <div className="card-title">
      <div>
        <h2>{title}</h2>
        {meta === undefined ? null : <span>{meta}</span>}
      </div>
      {actions === undefined ? null : <div className="toolbar">{actions}</div>}
    </div>
  )
}

export function EmptyState({ children }: { readonly children: ReactNode }) {
  return <div className="empty-state">{children}</div>
}

export function ErrorBanner({ message }: { readonly message: string | null }) {
  if (message === null) {
    return null
  }
  return <div className="error-banner">{message}</div>
}
