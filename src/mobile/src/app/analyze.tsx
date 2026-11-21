// Self-analysis screen (Phase 4 Stage C): analyse YOUR OWN posts, with consent.
// Reached from Profile. The model estimates your occupation + suggests interests.
import { router, Stack } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AnalyzeResult, api, ApiError } from '../lib/api';
import { useSession } from '../lib/session';
import { colors, space } from '../lib/theme';
import { Button, Card, Chip, ErrorText, Field, Muted, Title } from '../lib/ui';

export default function AnalyzeScreen() {
  const { token } = useSession();
  const [text, setText] = useState('');
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    if (!token) return;
    const posts = text.split('\n').map((l) => l.trim()).filter(Boolean);
    if (posts.length === 0) return setError('Paste a few of your own posts, one per line.');
    if (!consent) return setError('Please tick the consent box first.');
    setError(null);
    setBusy(true);
    try {
      setResult(await api.analyzeSelf(token, { posts }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not analyse.');
    } finally {
      setBusy(false);
    }
  }

  const occ = result?.occupation;
  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <Stack.Screen options={{ headerShown: true, title: 'Analyse my account' }} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Title>Analyse your own posts</Title>
        <Muted>
          Paste some of your OWN social posts (one per line). The model estimates your
          likely occupation and suggests interests. Nothing you paste is stored.
        </Muted>

        <Field
          label="Your posts (one per line)"
          value={text}
          onChangeText={setText}
          placeholder={'exam tomorrow, so much to study\ncollege fest was amazing\ncleared my backlog!'}
          multiline
          numberOfLines={6}
          style={{ minHeight: 120, textAlignVertical: 'top' }}
          autoCapitalize="none"
        />

        <Button
          title={consent ? '☑  I consent to analysing my own posts' : '☐  I consent to analysing my own posts'}
          kind="secondary"
          onPress={() => setConsent((c) => !c)}
        />
        <ErrorText message={error} />
        <Button title="Analyse" onPress={analyze} loading={busy} disabled={!consent} />

        {occ && (
          <Card>
            <Text style={styles.h}>Estimated occupation</Text>
            <Text style={styles.big}>
              {occ.label} · {(occ.confidence * 100).toFixed(0)}% ({occ.basis})
            </Text>
            {Object.entries(occ.probabilities)
              .sort((a, b) => b[1] - a[1])
              .map(([k, v]) => (
                <View key={k} style={styles.row}>
                  <Text style={styles.k}>{k}</Text>
                  <Text style={styles.v}>{(v * 100).toFixed(0)}%</Text>
                </View>
              ))}
            <Muted>Why: {occ.reasons.join(' · ')}</Muted>
            <Text style={[styles.h, { marginTop: space.sm }]}>Suggested interests</Text>
            <View style={styles.chips}>
              {result.suggested_interests.map((i) => <Chip key={i} text={i} />)}
            </View>
            <Muted>Model: {result.model}. {result.note}</Muted>
          </Card>
        )}

        <Button title="Back to profile" kind="secondary" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.md },
  h: { fontSize: 16, fontWeight: '700', color: colors.text },
  big: { fontSize: 20, fontWeight: '700', color: colors.primary },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 1 },
  k: { color: colors.text, fontSize: 15 },
  v: { color: colors.muted, fontSize: 15 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
