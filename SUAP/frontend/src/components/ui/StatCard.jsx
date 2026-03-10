/**
 * Card de estatística para o Dashboard.
 */
export default function StatCard({ label, value, icon: Icon, color = '#1351B4', loading }) {
  return (
    <div className="stat-card" style={{ borderColor: color }}>
      <div className="stat-card__icon" style={{ background: color }}>
        {Icon && <Icon size={24} color="#fff" />}
      </div>
      <div className="stat-card__body">
        {loading ? (
          <div className="skeleton-line" />
        ) : (
          <strong className="stat-card__value">{value ?? '—'}</strong>
        )}
        <span className="stat-card__label">{label}</span>
      </div>
    </div>
  )
}
