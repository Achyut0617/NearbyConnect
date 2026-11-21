// Area tab (Phase 4 Stage A+B): type a place -> trusted facts + aggregate trends.
// Everything shown here is about the AREA, never individual people.
import { useState } from 'react';
import { Keyboard, ScrollView, StyleSheet, Text, View } from 'react-native';

import { api, ApiError, AreaTrendsResult } from '../../lib/api';
import { useSession } from '../../lib/session';
import { colors, space } from '../../lib/theme';
import { Button, Card, Chip, ErrorText, Field, Muted } from '../../lib/ui';

export default function AreaScreen() {
  const { token } = useSession();
  const [place, setPlace] = useState('');
  const [result, setResult] = useState<AreaTrendsResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    if (!token || !place.trim()) return;
    Keyboard.dismiss();
    setError(null);
    setBusy(true);
    setResult(null);
    try {
      setResult(await api.areaTrends(token, place.trim()));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not look up that place.');
    } finally {
      setBusy(false);
    }
  }

  const trends = result?.trends;
  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled">
      <Field
        label="Explore an area"
        value={place}
        onChangeText={setPlace}
        placeholder="e.g. Loni Kalbhor, Pune"
        autoCapitalize="words"
        onSubmitEditing={search}
      />
      <Button title="Explore" onPress={search} loading={busy} />
      <ErrorText message={error} />

      {result && (
        <>
          <Card>
            <Text style={styles.h}>
              {result.facts.name ?? place}
              {result.facts.state ? ` · ${result.facts.state}` : ''}
            </Text>
            {result.facts.summary ? <Muted>{result.facts.summary}</Muted> : <Muted>No description found.</Muted>}
            <Muted>Sources: {result.facts.sources.join(', ')}</Muted>
          </Card>

          <Card>
            <Text style={styles.h}>Area keywords</Text>
            <View style={styles.chips}>
              {result.terms.keywords.slice(0, 12).map((k) => <Chip key={k} text={k} />)}
            </View>
            {result.terms.hashtags.length > 0 && (
              <View style={styles.chips}>
                {result.terms.hashtags.slice(0, 10).map((h) => <Chip key={h} text={h} />)}
              </View>
            )}
          </Card>

          <Card>
            <Text style={styles.h}>Social trends (aggregate only)</Text>
            {trends && trends.sources_used.length > 0 ? (
              <>
                <Muted>
                  From {trends.total_posts} public posts on {trends.sources_used.join(', ')} ·
                  mood: {trends.sentiment.mood}
                </Muted>
                {trends.topics.length > 0 ? (
                  trends.topics.slice(0, 10).map((t) => (
                    <View key={t.term} style={styles.row}>
                      <Text style={styles.term}>{t.term}</Text>
                      <Text style={styles.count}>{t.distinct_authors} people</Text>
                    </View>
                  ))
                ) : (
                  <Muted>{trends.note || 'Not enough distinct accounts to show topics yet.'}</Muted>
                )}
              </>
            ) : (
              <Muted>
                No trend sources connected. Add free Reddit / YouTube API keys (see
                docs/API_KEYS.md) to enable this.
              </Muted>
            )}
            {result.sources_skipped && (
              <Muted>Skipped: {Object.keys(result.sources_skipped).join(', ')}</Muted>
            )}
          </Card>

          <Muted>
            This view never lists individual accounts. A topic appears only if many
            different people posted it.
          </Muted>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: space.lg, gap: space.md },
  h: { fontSize: 17, fontWeight: '700', color: colors.text },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 2 },
  term: { color: colors.text, fontSize: 15 },
  count: { color: colors.muted, fontSize: 14 },
});
