// First-run flow: 1) what the app does + privacy promises, 2) sign up, 3) GPS permission.
import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { api, ApiError, parseInterests } from '../lib/api';
import { requestPermission } from '../lib/location';
import { useSession } from '../lib/session';
import { colors, space } from '../lib/theme';
import { Button, Card, ErrorText, Field, Muted, Title } from '../lib/ui';

type Step = 'welcome' | 'signup' | 'location';

export default function Onboarding() {
  const { signIn } = useSession();
  const [step, setStep] = useState<Step>('welcome');
  const [name, setName] = useState('');
  const [interests, setInterests] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [denied, setDenied] = useState(false);

  async function handleSignUp() {
    setError(null);
    const tags = parseInterests(interests);
    if (!name.trim()) return setError('Please enter a name.');
    if (tags.length === 0) return setError('Add at least one interest, e.g. AI, startups.');
    setBusy(true);
    try {
      const user = await api.signUp(name.trim());
      await api.setInterests(user.token, tags);
      await signIn(user.token);
      setStep('location');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  async function handleAllowLocation() {
    setBusy(true);
    try {
      const ok = await requestPermission();
      if (ok) router.replace('/');
      else setDenied(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {step === 'welcome' && (
            <>
              <Title>Welcome to NearbyConnect</Title>
              <Muted>
                Discover places near you that match your interests, and meet other NearbyConnect
                users nearby who share them.
              </Muted>
              <Card>
                <Text style={styles.cardTitle}>Our privacy promises</Text>
                <PromiseRow text="We only use your location while the app is open. Never in the background." />
                <PromiseRow text="Other users never see your location unless you turn on sharing, and even then only a rough distance." />
                <PromiseRow text="We don't keep a history of where you've been." />
                <PromiseRow text="We never look up or contact people on other social apps for you." />
              </Card>
              <Button title="Get started" onPress={() => setStep('signup')} />
            </>
          )}

          {step === 'signup' && (
            <>
              <Title>About you</Title>
              <Muted>Your name is shown to people you connect with. Interests decide what we suggest.</Muted>
              <Field
                label="Display name"
                value={name}
                onChangeText={setName}
                placeholder="e.g. Achyut"
                maxLength={50}
                autoCapitalize="words"
              />
              <Field
                label="Interests (separate with commas)"
                value={interests}
                onChangeText={setInterests}
                placeholder="e.g. AI, startups, coffee, reading"
                autoCapitalize="none"
              />
              <ErrorText message={error} />
              <Button title="Continue" onPress={handleSignUp} loading={busy} />
            </>
          )}

          {step === 'location' && (
            <>
              <Title>Use your location?</Title>
              <Muted>
                NearbyConnect needs your location while the app is open to find places around you.
                This does NOT share your location with other users. That's a separate switch on
                the People tab, and it's off by default.
              </Muted>
              {!denied ? (
                <Button title="Allow location while using the app" onPress={handleAllowLocation} loading={busy} />
              ) : (
                <Card>
                  <Text style={styles.cardTitle}>Location is off</Text>
                  <Muted>
                    No problem. You can turn it on later in your phone's Settings. The Feed needs it
                    to find nearby places.
                  </Muted>
                </Card>
              )}
              <Button title={denied ? 'Continue' : 'Not now'} kind="secondary" onPress={() => router.replace('/')} />
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function PromiseRow({ text }: { text: string }) {
  return (
    <View style={styles.promise}>
      <Text style={styles.tick}>✓</Text>
      <Muted>{text}</Muted>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.xl, gap: space.lg, flexGrow: 1, justifyContent: 'center' },
  cardTitle: { fontSize: 16, fontWeight: '600', color: colors.text },
  promise: { flexDirection: 'row', gap: space.sm, paddingRight: space.lg },
  tick: { color: colors.success, fontWeight: '700', fontSize: 14, lineHeight: 20 },
});
