/** Placeholder rows shaped like list items (avatar + two lines) while data loads. */
export function SkeletonList({ rows = 6, avatar = 44 }: { rows?: number; avatar?: number }) {
  return (
    <div className="skeleton-list" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton-row">
          <span className="skeleton skeleton-circle" style={{ width: avatar, height: avatar }} />
          <span className="skeleton-lines">
            <span className="skeleton skeleton-line" style={{ width: `${55 + ((i * 17) % 35)}%` }} />
            <span className="skeleton skeleton-line short" style={{ width: `${30 + ((i * 11) % 25)}%` }} />
          </span>
        </div>
      ))}
    </div>
  );
}
