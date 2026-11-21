// Root of the app: provides the login session to every screen.
import { router, Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { configureNotifications, onNotificationTap } from '../lib/push';
import { SessionProvider } from '../lib/session';

configureNotifications(); // how to show notifications while the app is open

export default function RootLayout() {
  // Tapping a notification opens the screen it points to (e.g. Requests).
  useEffect(
    () =>
      onNotificationTap((screen) => {
        if (screen === 'requests') router.push('/requests');
      }),
    [],
  );

  return (
    <SessionProvider>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="analyze" />
      </Stack>
    </SessionProvider>
  );
}
