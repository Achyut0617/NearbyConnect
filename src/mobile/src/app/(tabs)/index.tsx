// Feed tab: places near you, ranked by your interests (calls POST /nearby).
import { ReactNode, useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Linking,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { api, ApiError, Place } from '../../lib/api';
import { getCurrentCoords, getPermission, PermissionState, requestPermission } from '../../lib/location';
import { useSession } from '../../lib/session';
import { colors, space } from '../../lib/theme';
import { Button, Card, Chip, Muted, RadiusPicker, formatDistance } from '../../lib/ui';

const RADII = [500, 1000, 2000, 5000];

type Status = 'idle' | 'loading' | 'done' | 'error';

export default function FeedScreen() {
  const { token, me } = useSession();
  const [permission, setPermission] = useState<PermissionState | null>(null);
  const [radius, setRadius] = useState(1000);
  const [places, setPlaces] = useState<Place[]>([]);
  const [interestsUsed, setInterestsUsed] = useState<string[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const requestId = useRef(0); // ignore answers from older, slower requests

  const load = useCallback(async () => {
    if (!token) return;
    const myId = ++requestId.current;
    setError(null);
    setStatus('loading');
    try {
      const { lat, lon } = await getCurrentCoords(); // kept in memory only
      const result = await api.nearby(token, lat, lon, radius);
      if (myId !== requestId.current) return;
      setPlaces(result.places);
      setInterestsUsed(result.interests_used);
      setStatus('done');
    } catch (e) {
      if (myId !== requestId.current) return;
      setStatus('error');
      if (e instanceof ApiError && e.status === 503) {
        setError('The free map service is busy right now. Pull down to try again in a minute.');
      } else if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError("Couldn't get your location. Check that location is turned on.");
      }
    }
  }, [token, radius]);

  // Check permission once when the screen opens.
  useEffect(() => {
    getPermission().then(setPermission).catch(() => setPermission('undetermined'));
  }, []);

  // Load when permission is granted, the radius changes, or interests change.
  const interestsKey = (me?.interests ?? []).join(',');
  useEffect(() => {
    if (permission === 'granted') load();
  }, [permission, load, interestsKey]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  async function allowLocation() {
    const ok = await requestPermission();
    setPermission(ok ? 'granted' : 'denied');
  }

  if (permission === null) {
    return <Centered><ActivityIndicator /></Centered>;
  }

  if (permission !== 'granted') {
    return (
      <View style={styles.page}>
        <Card>
          <Text style={styles.cardTitle}>Location needed</Text>
          <Muted>
            To show places near you, NearbyConnect needs your location while the app is open. It is
            not shared with other users.
          </Muted>
          <Button title="Allow location" onPress={allowLocation} />
          {permission === 'denied' && (
            <Button title="Open phone Settings" kind="secondary" onPress={() => Linking.openSettings()} />
          )}
        </Card>
      </View>
    );
  }

  return (
    <FlatList
      style={{ backgroundColor: colors.bg }}
      contentContainerStyle={styles.list}
      data={status === 'error' ? [] : places}
      keyExtractor={(p) => p.osm_id}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      ListHeaderComponent={
        <View style={{ gap: space.md }}>
          <RadiusPicker options={RADII} value={radius} onChange={setRadius} />
          {status === 'done' && interestsUsed.length === 0 && (
            <Muted>Tip: add interests in the Profile tab to get better suggestions.</Muted>
          )}
          {status === 'loading' && !refreshing && (
            <Card style={{ alignItems: 'center' }}>
              <ActivityIndicator />
              <Muted>Finding places near you… The free map servers can take up to a minute.</Muted>
            </Card>
          )}
          {status === 'error' && error && (
            <Card>
              <Text style={[styles.cardTitle, { color: colors.danger }]}>Couldn't load places</Text>
              <Muted>{error}</Muted>
              <Button title="Try again" kind="secondary" onPress={load} />
            </Card>
          )}
        </View>
      }
      ListEmptyComponent={
        status === 'done' ? <Muted>No named places found in this radius. Try a bigger one.</Muted> : undefined
      }
      renderItem={({ item }) => <PlaceCard place={item} />}
    />
  );
}

function PlaceCard({ place }: { place: Place }) {
  const openMaps = () =>
    Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${place.lat},${place.lon}`);
  return (
    <Card>
      <View style={styles.titleRow}>
        <Text style={styles.placeName} numberOfLines={2}>{place.name}</Text>
        <Text style={styles.distance}>{formatDistance(place.distance_m)}</Text>
      </View>
      <View style={{ flexDirection: 'row' }}>
        <Chip text={place.category.replace('_', ' ')} />
      </View>
      {place.reasons.length > 0 && (
        <Muted>Why this? {place.reasons.join(' · ')}</Muted>
      )}
      <Button title="Open in Maps" kind="secondary" onPress={openMaps} />
    </Card>
  );
}

function Centered({ children }: { children: ReactNode }) {
  return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>{children}</View>;
}

const styles = StyleSheet.create({
  page: { padding: space.lg },
  list: { padding: space.lg, gap: space.md },
  cardTitle: { fontSize: 16, fontWeight: '600', color: colors.text },
  titleRow: { flexDirection: 'row', justifyContent: 'space-between', gap: space.md },
  placeName: { flex: 1, fontSize: 17, fontWeight: '600', color: colors.text },
  distance: { color: colors.muted, fontSize: 14 },
});
