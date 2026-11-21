// Who is logged in, shared with every screen through React "context".
import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react';

import { api, ApiError, Me } from './api';
import { clearToken, loadToken, saveToken } from './storage';

type SessionValue = {
  ready: boolean;          // false while we're still reading the saved token
  token: string | null;
  me: Me | null;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);

  const loadMe = useCallback(async (t: string) => {
    try {
      setMe(await api.me(t));
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        // The server doesn't know this token (e.g. its database was reset).
        await clearToken();
        setToken(null);
        setMe(null);
      }
      // Other errors (server offline): keep the token and try again later.
    }
  }, []);

  useEffect(() => {
    (async () => {
      const saved = await loadToken();
      if (saved) {
        setToken(saved);
        await loadMe(saved);
      }
      setReady(true);
    })();
  }, [loadMe]);

  const signIn = useCallback(async (t: string) => {
    await saveToken(t);
    setToken(t);
    await loadMe(t);
  }, [loadMe]);

  const signOut = useCallback(async () => {
    await clearToken();
    setToken(null);
    setMe(null);
  }, []);

  const refreshMe = useCallback(async () => {
    if (token) await loadMe(token);
  }, [token, loadMe]);

  return (
    <SessionContext.Provider value={{ ready, token, me, signIn, signOut, refreshMe }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error('useSession must be used inside <SessionProvider>');
  return value;
}
