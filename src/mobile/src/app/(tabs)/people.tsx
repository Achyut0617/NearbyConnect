// People tab: opt-in location sharing + nearby NearbyConnect users with shared interests.
// Only NearbyConnect users who turned sharing on ever appear here.
import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Platform,
  RefreshControl,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';

import { api, ApiError, NearbyUser } from '../../lib/api';
import { getCurrentCoords, getPermission, requestPermission } from '../../lib/location';
import { useSession } from '../../lib/session';
import { colors, space } from '../../lib/theme';
import { Button, Card, Chip, ErrorText, Muted, RadiusPicker, formatDistance } from '../../lib/ui';

const RADII = [1000, 2000, 5000];

/** Ask "are you sure?". Uses window.confirm on web, Alert on phones. */
function confirm(title: string, message: string): Promise<boolean> {
  if (Platform.OS === 'web') return Promise.resolve(globalThis.confirm?.(`${title}\n\n${message}`) ?? false);
  return new Promise((resolve) =>
    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
      { text: 'Turn on', onPress: () => resolve(true) },
    ]),
  );
}

export default function PeopleScreen() {
  const { token } = useSession();
  const [sharing, setSharing] = useState<boolean | null>(null); // null = loading
  const [switchBusy, setSwitchBusy] = useState(false);
  const [radius, setRadius] = useState(2000);
  const [users, setUsers] = useState<NearbyUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requested, setRequested] = useState<Record<number, string>>({}); // user_id -> note

  /** While sharing is on, send a fresh location (keeps it from going stale after 2 h). */
  const refreshMyLocation = useCallback(async () => {
    if (!token) return;
    const { lat, lon } = await getCurrentCoords();
    await api.shareLocation(token, lat, lon);
  }, [token]);

  const loadUsers = useCallback(async () => {
    if (!token) return;
    setError(null);
    setLoadingUsers(true);
    try {
      await refreshMyLocation();
      const res = await api.nearbyUsers(token, radius);
      setUsers(res.users);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't get your location.");
    } finally {
      setLoadingUsers(false);
    }
  }, [token, radius, refreshMyLocation]);

  // When the tab opens: read sharing status from the server; reload if sharing.
  useFocusEffect(
    useCallback(() => {
      if (!token) return;
      api
        .sharingStatus(token)
        .then((s) => setSharing(s.sharing))
        .catch((e) => {
          setSharing(false);
          setError(e instanceof ApiError ? e.message : 'Could not load sharing status.');
        });
    }, [token]),
  );

  useEffect(() => {
    if (sharing) loadUsers();
  }, [sharing, loadUsers]);

  async function toggleSharing(next: boolean) {
    if (!token) return;
    setError(null);
    if (next) {
      const ok = await confirm(
        'Share your location?',
        'Other NearbyConnect users who also share and have an interest in common will see your name, ' +
          'your shared interests and a ROUGH distance (like "400 m"). Never your exact location. ' +
          'It stops being used after 2 hours, and you can turn it off at any time.',
      );
      if (!ok) return;
      if ((await getPermission()) !== 'granted' && !(await requestPermission())) {
        setError('Location permission is needed to share your location.');
        return;
      }
    }
    setSwitchBusy(true);
    try {
      if (next) {
        await refreshMyLocation();
        setSharing(true);
      } else {
        await api.stopSharing(token); // the server erases your stored location
        setSharing(false);
        setUsers([]);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't get your location.");
    } finally {
      setSwitchBusy(false);
    }
  }

  async function connect(user: NearbyUser) {
    if (!token) return;
    try {
      await api.sendConnect(token, user.user_id);
      setRequested((r) => ({ ...r, [user.user_id]: 'Request sent' }));
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Could not send request.';
      setRequested((r) => ({ ...r, [user.user_id]: msg }));
    }
  }

  async function onRefresh() {
    setRefreshing(true);
    await loadUsers();
    setRefreshing(false);
  }

  const header = (
    <View style={{ gap: space.md }}>
      <Card>
        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Share my location with nearby NearbyConnect users</Text>
          {sharing === null || switchBusy ? (
            <ActivityIndicator />
          ) : (
            <Switch value={sharing} onValueChange={toggleSharing} accessibilityLabel="Share my location" />
          )}
        </View>
        <Muted>
          {sharing
            ? 'On. Others see only your name, shared interests and a rough distance.'
            : 'Off. Nobody can see you, and you can\'t see others. It works both ways.'}
        </Muted>
      </Card>
      <ErrorText message={error} />
      {sharing && <RadiusPicker options={RADII} value={radius} onChange={setRadius} />}
      {sharing && loadingUsers && !refreshing && <ActivityIndicator />}
    </View>
  );

  return (
    <FlatList
      style={{ backgroundColor: colors.bg }}
      contentContainerStyle={styles.list}
      data={sharing ? users : []}
      keyExtractor={(u) => String(u.user_id)}
      ListHeaderComponent={header}
      refreshControl={sharing ? <RefreshControl refreshing={refreshing} onRefresh={onRefresh} /> : undefined}
      ListEmptyComponent={
        sharing && !loadingUsers ? (
          <Muted>
            No one with shared interests is sharing nearby right now. Pull down to check again, or try a
            bigger radius.
          </Muted>
        ) : undefined
      }
      renderItem={({ item }) => (
        <Card>
          <View style={styles.titleRow}>
            <Text style={styles.name}>{item.display_name}</Text>
            <Text style={styles.distance}>~{formatDistance(item.approx_distance_m)}</Text>
          </View>
          <View style={styles.chips}>
            {item.shared_interests.map((i) => (
              <Chip key={i} text={i} />
            ))}
          </View>
          {requested[item.user_id] ? (
            <Muted>{requested[item.user_id]}</Muted>
          ) : (
            <Button title="Connect" onPress={() => connect(item)} />
          )}
        </Card>
      )}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: space.lg, gap: space.md },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  switchLabel: { flex: 1, fontSize: 16, fontWeight: '600', color: colors.text },
  titleRow: { flexDirection: 'row', justifyContent: 'space-between', gap: space.md },
  name: { flex: 1, fontSize: 17, fontWeight: '600', color: colors.text },
  distance: { color: colors.muted, fontSize: 14 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
