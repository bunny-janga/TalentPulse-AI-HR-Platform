import { cx } from '../../utils/cx.js';
import { Skeleton } from './Skeleton.jsx';

/**
 * Data table with skeleton rows while loading and staggered row entrance.
 * columns: [{ key, header, render?(row), align?: 'right'|'center', className? }]
 */
export function Table({ columns, rows, rowKey = 'id', loading = false, skeletonRows = 5, empty = null, onRowClick, caption, children }) {
  if (children) {
    return (
      <div className="table-wrap">
        <table className="table">
          {caption ? <caption className="sr-only">{caption}</caption> : null}
          {children}
        </table>
      </div>
    );
  }

  if (!loading && (!rows || rows.length === 0) && empty) return empty;
  if (!columns) return null;
  return (
    <div className="table-wrap">
      <table className="table">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className={cx(c.align && `is-${c.align}`)}>{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: skeletonRows }, (_, i) => (
                <tr key={`sk-${i}`} style={{ '--i': i }} aria-hidden="true">
                  {columns.map((c) => (
                    <td key={c.key}><Skeleton h={14} w={`${55 + ((i * 17 + c.key.length * 7) % 40)}%`} /></td>
                  ))}
                </tr>
              ))
            : rows.map((row, i) => {
                const clickable = Boolean(onRowClick);
                return (
                  <tr
                    key={row[rowKey]}
                    style={{ '--i': Math.min(i, 14) }}
                    data-clickable={clickable || undefined}
                    tabIndex={clickable ? 0 : undefined}
                    onClick={clickable ? () => onRowClick(row) : undefined}
                    onKeyDown={clickable ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onRowClick(row); } } : undefined}
                  >
                    {columns.map((c) => (
                      <td key={c.key} className={cx(c.align && `is-${c.align}`, c.className)}>
                        {c.render ? c.render(row) : row[c.key]}
                      </td>
                    ))}
                  </tr>
                );
              })}
        </tbody>
      </table>
    </div>
  );
}
