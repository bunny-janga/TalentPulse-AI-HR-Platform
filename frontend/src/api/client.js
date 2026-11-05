// Thin fetch wrapper: token injection, JSON/multipart bodies, normalised errors, AbortController support.

let token = null;
let onUnauthorized = null;

/** Called by the auth provider whenever the session token changes. */
export const setToken = (value) => { token = value; };
/** Registers the callback that runs when an authenticated request returns 401. */
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

/**
 * kind: unauthorized | forbidden | notfound | conflict | validation | server | network | aborted | error
 */
export class ApiError extends Error {
  constructor(kind, status, message, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

const KIND_BY_STATUS = { 401: 'unauthorized', 403: 'forbidden', 404: 'notfound', 409: 'conflict', 422: 'validation' };

const FALLBACK_MESSAGE = {
  unauthorized: 'Your session has expired. Please sign in again.',
  forbidden: 'You do not have access to this area.',
  notfound: 'We could not find what you were looking for.',
  server: 'The server hit a problem. Please try again shortly.',
};

/** FastAPI returns `detail` as a string or as a list of validation items. */
function messageFrom(detail, fallback) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        if (!d?.msg) return String(d);
        const field = (d.loc || []).filter((part) => part !== 'body').join('.');
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join('; ');
  }
  return fallback;
}

function toQueryString(query) {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value));
  });
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

export async function request(path, { method = 'GET', body, form, query, signal, auth = true } = {}) {
  const headers = { Accept: 'application/json' };
  let payload;
  if (form) {
    payload = form; // the browser sets the multipart boundary itself
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${path}${query ? toQueryString(query) : ''}`, { method, headers, body: payload, signal });
  } catch (err) {
    if (err?.name === 'AbortError') throw new ApiError('aborted', 0, 'Request cancelled');
    throw new ApiError('network', 0, 'Cannot reach the server. Check your connection and try again.');
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }
  if (response.ok) return data;

  const kind = KIND_BY_STATUS[response.status] ?? (response.status >= 500 ? 'server' : 'error');
  if (kind === 'unauthorized' && auth && onUnauthorized) onUnauthorized();
  const detail = data && typeof data === 'object' ? data.detail ?? null : null;
  throw new ApiError(kind, response.status, messageFrom(detail, FALLBACK_MESSAGE[kind] ?? `Request failed (${response.status})`), detail);
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  put: (path, body, opts) => request(path, { ...opts, method: 'PUT', body }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  del: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
  upload: (path, form, opts) => request(path, { ...opts, method: 'POST', form }),
};
