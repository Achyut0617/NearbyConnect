// Requests tab: answer incoming requests, see outgoing ones, list connections.
import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api, ApiError, Connection, ConnectRequest } from '../../lib/api';
import { useSession } from '../../lib/session';
import { colors, space } from '../../lib/theme';
import { Button, Card, Chip, ErrorText, Muted } from '../../lib/ui';

export default function RequestsScreen() {
  const { token } = useSession();
  const [incoming, setIncoming] = useState<ConnectRequest[]>([]);
  const [outgoing, setOutgoing] = useState<ConnectRequest[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setError(null);
    try {
      const [reqs, conns] = await Promise.all([api.listRequests(token), api.connections(token)]);
      setIncoming(reqs.incoming);
      setOutgoing(reqs.outgoing);
      setConnections(conns.connections);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load requests.');
    }
  }, [token]);

  // Reload every time the tab is opened.
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  async function answer(id: number, action: 'accept' | 'decline') {
    if (!token) return;
    setBusyId(id);
    try {
      await (action === 'accept' ? api.accept(token, id) : api.decline(token, id));
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not update the request.');
    } finally {
      setBusyId(null);
    }
  }

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  return (
    <ScrollView
      style={{ backgroundColor: colors.bg }}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <ErrorText message={error} />

      <Text style={styles.section}>Requests for you</Text>
      {incoming.length === 0 && <Muted>No new requests.</Muted>}
      {incoming.map((r) => (
        <Card key={r.id}>
          <Text style={styles.name}>{r.from_user.display_name}</Text>
          <Muted>wants to connect with you.</Muted>
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Button title="Accept" onPress={() => answer(r.id, 'accept')} loading={busyId === r.id} />
            </View>
            <View style={{ flex: 1 }}>
              <Button
                title="Decline"
                kind="secondary"
                onPress={() => answer(r.id, 'decline')}
                disabled={busyId === r.id}
              />
            </View>
          </View>
        </Card>
      ))}

      <Text style={styles.section}>Sent by you</Text>
      {outgoing.length === 0 && <Muted>No pending requests.</Muted>}
      {outgoing.map((r) => (
        <Card key={r.id}>
          <Text style={styles.name}>{r.to_user.display_name}</Text>
          <Muted>Waiting for them to accept.</Muted>
        </Card>
      ))}

      <Text style={styles.section}>Your connections</Text>
      {connections.length === 0 && <Muted>No connections yet. Find people on the People tab.</Muted>}
      {connections.map((c) => (
        <Card key={c.user_id}>
          <Text style={styles.name}>{c.display_name}</Text>
          <View style={styles.chips}>
            {c.interests.map((i) => (
              <Chip key={i} text={i} />
            ))}
          </View>
        </Card>
      ))}
      {connections.length > 0 && (
        <Muted>
          Want to stay in touch elsewhere? Swap contact details yourselves. NearbyConnect never
          follows or messages anyone on other apps for you.
        </Muted>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: space.lg, gap: space.md },
  section: { fontSize: 18, fontWeight: '700', color: colors.text, marginTop: space.sm },
  name: { fontSize: 17, fontWeight: '600', color: colors.text },
  row: { flexDirection: 'row', gap: space.md },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
