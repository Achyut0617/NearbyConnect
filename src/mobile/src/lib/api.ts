// Every call the app makes to the NearbyConnect backend lives here.

// Set in src/mobile/.env, e.g. EXPO_PUBLIC_API_URL=http://192.168.1.10:8000
export const API_URL = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

// /nearby can take up to ~60 s when the free OSM servers are busy.
const TIMEOUT_MS = 90_000;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Options = { method?: string; body?: unknown; token?: string | null };

async function request<T>(path: string, { method = 'GET', body, token }: Options = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch {
    throw new ApiError(0, `Can't reach the server at ${API_URL}. Is the backend running?`);
  } finally {
    clearTimeout(timer);
  }

  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(res.status, readableError(data) ?? `Server error (${res.status})`);
  }
  return data as T;
}

/** FastAPI errors are either {detail: "text"} or {detail: [{msg: "..."}]}. */
function readableError(data: unknown): string | null {
  const d = (data as { detail?: unknown } | null)?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && typeof d[0]?.msg === 'string') return d[0].msg;
  return null;
}

// ---------- Types (match the backend's JSON) ----------

export type Me = { id: number; display_name: string; interests: string[] };

export type Place = {
  osm_id: string;
  name: string;
  category: string;
  type: string;
  lat: number;
  lon: number;
  score: number;
  reasons: string[];
  distance_m: number | null;
};

export type NearbyResult = {
  radius_m: number;
  interests_used: string[];
  count: number;
  places: Place[];
};

export type NearbyUser = {
  user_id: number;
  display_name: string;
  shared_interests: string[];
  approx_distance_m: number;
};

export type SharingStatus = { sharing: boolean; updated_at: string | null; fresh: boolean };

export type UserRef = { id: number; display_name: string };

export type ConnectRequest = {
  id: number;
  from_user: UserRef;
  to_user: UserRef;
  status: 'pending' | 'accepted' | 'declined';
  created_at: string | null;
  responded_at: string | null;
};

export type Connection = {
  user_id: number;
  display_name: string;
  interests: string[];
  since: string | null;
};

// ---------- Endpoints ----------

export const api = {
  health: () => request<{ status: string }>('/health'),

  signUp: (display_name: string) =>
    request<{ id: number; display_name: string; token: string }>('/users', {
      method: 'POST',
      body: { display_name },
    }),

  me: (token: string) => request<Me>('/me', { token }),

  setInterests: (token: string, interests: string[]) =>
    request<{ interests: string[] }>('/me/interests', { method: 'PUT', token, body: { interests } }),

  nearby: (token: string, lat: number, lon: number, radius_m: number) =>
    request<NearbyResult>('/nearby', { method: 'POST', token, body: { lat, lon, radius_m } }),

  sharingStatus: (token: string) => request<SharingStatus>('/me/location', { token }),

  shareLocation: (token: string, lat: number, lon: number) =>
    request<SharingStatus>('/me/location', {
      method: 'PUT',
      token,
      body: { consent: true, lat, lon },
    }),

  stopSharing: (token: string) =>
    request<SharingStatus>('/me/location', { method: 'DELETE', token }),

  nearbyUsers: (token: string, radius_m: number) =>
    request<{ radius_m: number; count: number; users: NearbyUser[] }>(
      `/me/nearby-users?radius_m=${radius_m}`,
      { token },
    ),

  sendConnect: (token: string, to_user_id: number) =>
    request<ConnectRequest>('/connect-requests', { method: 'POST', token, body: { to_user_id } }),

  listRequests: (token: string) =>
    request<{ incoming: ConnectRequest[]; outgoing: ConnectRequest[] }>('/connect-requests', { token }),

  accept: (token: string, id: number) =>
    request<ConnectRequest>(`/connect-requests/${id}/accept`, { method: 'POST', token }),

  decline: (token: string, id: number) =>
    request<ConnectRequest>(`/connect-requests/${id}/decline`, { method: 'POST', token }),

  connections: (token: string) => request<{ connections: Connection[] }>('/connections', { token }),

  setPushToken: (token: string, pushToken: string) =>
    request<{ notifications: boolean }>('/me/push-token', {
      method: 'PUT',
      token,
      body: { token: pushToken },
    }),

  clearPushToken: (token: string) =>
    request<{ notifications: boolean }>('/me/push-token', { method: 'DELETE', token }),
};

/** "AI, startups,  coffee" -> ["AI", "startups", "coffee"] */
export function parseInterests(text: string): string[] {
  return text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}
