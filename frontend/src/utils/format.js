// Formatting and small domain helpers shared across features.

const dateFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
const dateTimeFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
const numberFmt = new Intl.NumberFormat();

/** Backend datetimes are naive UTC strings; add a Z so the browser converts them correctly. */
const parse = (value) => {
  if (!value) return null;
  const str = String(value);
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(str);
  const d = new Date(str.length === 10 || hasZone ? str : `${str}Z`);
  return Number.isNaN(d.getTime()) ? null : d;
};

export const formatDate = (value) => { const d = parse(value); return d ? dateFmt.format(d) : '—'; };
export const formatDateTime = (value) => { const d = parse(value); return d ? dateTimeFmt.format(d) : '—'; };
export const formatNumber = (value, decimals = 0) =>
  Number.isFinite(value) ? (decimals ? value.toFixed(decimals) : numberFmt.format(Math.round(value))) : '—';

export const initials = (name = '') =>
  name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('') || '?';

/** Inclusive calendar-day count between two yyyy-mm-dd strings; 0 when invalid or reversed. */
export function daysBetween(start, end) {
  if (!start || !end) return 0;
  const a = new Date(`${start}T00:00:00`);
  const b = new Date(`${end}T00:00:00`);
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return 0;
  return Math.round((b - a) / 86400000) + 1;
}

/** Mon-Fri days between two yyyy-mm-dd strings, inclusive (mirrors the server's leave-day count). */
export function weekdaysBetween(start, end) {
  if (!start || !end) return 0;
  const a = new Date(`${start}T00:00:00`);
  const b = new Date(`${end}T00:00:00`);
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return 0;
  let n = 0;
  for (let d = new Date(a); d <= b; d.setDate(d.getDate() + 1)) {
    const wd = d.getDay();
    if (wd !== 0 && wd !== 6) n += 1;
  }
  return n;
}

/** Today as yyyy-mm-dd in local time. */
export const todayISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

export const ROLE_LABEL = { superadmin: 'Super Admin ★', admin: 'Admin', hr: 'HR', manager: 'Manager', employee: 'Employee' };

/** Risk band -> semantic tone + text label (status is never conveyed by colour alone). */
export const RISK_TONE = { LOW: 'ok', MEDIUM: 'warn', HIGH: 'danger' };
export const RISK_LABEL = { LOW: 'Low risk', MEDIUM: 'Medium risk', HIGH: 'High risk' };

/** Leave types the backend accepts, with short UI labels. */
export const LEAVE_TYPES = [
  { value: 'Casual Leave', label: 'Casual Leave (CL): personal and family' },
  { value: 'Sick Leave', label: 'Sick Leave (SL): medical' },
  { value: 'Earned Leave', label: 'Earned Leave (EL): planned vacation' },
  { value: 'Compensatory Off', label: 'Compensatory Off: weekend or holiday work' },
  { value: 'Bereavement Leave', label: 'Bereavement Leave' },
  { value: 'Paternity Leave', label: 'Paternity Leave' },
  { value: 'Maternity Leave', label: 'Maternity Leave' },
  { value: 'Unpaid Leave', label: 'Unpaid Leave' },
];
