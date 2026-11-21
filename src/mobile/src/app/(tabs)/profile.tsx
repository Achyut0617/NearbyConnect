// Profile tab: your name, edit interests, location permission status, sign out.
import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { Alert, Linking, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api, API_URL, ApiError, parseInterests } from '../../lib/api';
import { getPermission, PermissionState, requestPermission } from '../../lib/location';
import { useSession } from '../../lib/session';
import { colors, space } from '../../lib/theme';
import { Button, Card, Chip, ErrorText, Field, Muted } from '../../lib/ui';

export default function ProfileScreen() {
  const { token, me, refreshMe, signOut } = useSession();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [permission, setPermission] = useState<PermissionState | null>(null);

  // Re-check permission every time this tab is opened (user may have changed Settings).
  useFocusEffect(
    useCallback(() => {
      getPermission().then(setPermission).catch(() => setPermission(null));
    }, []),
  );

  async function saveInterests() {
    if (!token) return;
    setError(null);
    setBusy(true);
    try {
      await api.setInterests(token, parseInterests(draft));
      await refreshMe();
      setEditing(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not save.');
    } finally {
      setBusy(false);
    }
  }

  async function askPermission() {
    const ok = await requestPermission();
    setPermission(ok ? 'granted' : 'denied');
    if (!ok && Platform.OS !== 'web') {
      Alert.alert('Location is off', 'You can allow it in your phone Settings.', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Open Settings', onPress: () => Linking.openSettings() },
      ]);
    }
  }

  function confirmSignOut() {
    const doIt = () => void signOut();
    if (Platform.OS === 'web') return doIt();
    Alert.alert(
      'Sign out?',
      'Your account is tied to this device. Without the saved token you cannot sign back in to it.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign out', style: 'destructive', onPress: doIt },
      ],
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Card>
        <Text style={styles.name}>{me?.display_name ?? '…'}</Text>
        <Muted>Your interests</Muted>
        {!editing ? (
          <>
            <View style={styles.chips}>
              {(me?.interests ?? []).map((i) => (
                <Chip key={i} text={i} />
              ))}
              {me && me.interests.length === 0 && <Muted>None yet</Muted>}
            </View>
            <Button
              title="Edit interests"
              kind="secondary"
              onPress={() => {
                setDraft((me?.interests ?? []).join(', '));
                setEditing(true);
              }}
            />
          </>
        ) : (
          <>
            <Field label="Interests (comma separated)" value={draft} onChangeText={setDraft} autoCapitalize="none" />
            <ErrorText message={error} />
            <Button title="Save" onPress={saveInterests} loading={busy} />
            <Button title="Cancel" kind="secondary" onPress={() => setEditing(false)} />
          </>
        )}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>Location permission</Text>
        <Muted>
          {permission === 'granted'
            ? 'Allowed while the app is open.'
            : permission === 'denied'
              ? 'Not allowed. The Feed cannot find nearby places.'
              : 'Not decided yet.'}
        </Muted>
        {permission !== 'granted' && <Button title="Allow location" kind="secondary" onPress={askPermission} />}
      </Card>

      <Card>
        <Text style={styles.cardTitle}>About</Text>
        <Muted>Server: {API_URL}</Muted>
      </Card>

      <Button title="Sign out" kind="danger" onPress={confirmSignOut} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: space.lg, gap: space.lg },
  name: { fontSize: 20, fontWeight: '700', color: colors.text },
  cardTitle: { fontSize: 16, fontWeight: '600', color: colors.text },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
