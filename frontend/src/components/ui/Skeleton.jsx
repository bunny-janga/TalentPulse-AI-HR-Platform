import { cx } from '../../utils/cx.js';

/** Shimmering placeholder block. Decorative, so hidden from assistive tech. */
export function Skeleton({ w = '100%', h = 16, circle = false, className, style }) {
  return <span aria-hidden="true" className={cx('skeleton', circle && 'skeleton--circle', className)} style={{ width: w, height: h, ...style }} />;
}

export function SkeletonText({ lines = 3 }) {
  return (
    <div className="stack" style={{ '--gap': '10px' }} aria-hidden="true">
      {Array.from({ length: lines }, (_, i) => <Skeleton key={i} h={12} w={i === lines - 1 ? '62%' : '100%'} />)}
    </div>
  );
}

/** Generic card-grid skeleton used by route fallbacks. */
export function SkeletonCards({ count = 4, h = 132 }) {
  return (
    <div className="grid grid--auto" style={{ '--min': '240px' }} role="status" aria-label="Loading">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="card card--pad stack" style={{ '--i': i, '--gap': '14px' }} aria-hidden="true">
          <Skeleton w="40%" h={12} />
          <Skeleton w="64%" h={h / 3} />
          <Skeleton h={10} />
        </div>
      ))}
    </div>
  );
}
