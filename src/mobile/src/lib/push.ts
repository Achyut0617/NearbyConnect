// Push notifications (Step 14).
// IMPORTANT: remote push does NOT work inside the Expo Go app (Expo removed it in SDK 53).
// It needs a "development build" of NearbyConnect, plus an EAS project id in app.json.
import { isRunningInExpoGo } from 'expo';
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { api } from './api';

export type PushResult = 'enabled' | 'denied' | 'expo-go' | 'web' | 'no-project-id' | 'error';

/** How to show a notification that arrives while the app is open. Call once at startup. */
export function configureNotifications(): void {
  if (Platform.OS === 'web') return;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldPlaySound: false,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
}

/** Call `onOpen(screen)` when the user taps a notification. Returns an unsubscribe function. */
export function onNotificationTap(onOpen: (screen: string) => void): () => void {
  if (Platform.OS === 'web') return () => {};
  const sub = Notifications.addNotificationResponseReceivedListener((response) => {
    const screen = response.notification.request.content.data?.screen;
    if (typeof screen === 'string') onOpen(screen);
  });
  return () => sub.remove();
}

/**
 * Get this phone's Expo push token and send it to our backend.
 * ask=false: never show a permission popup (used silently at startup).
 * ask=true: show the popup if needed (used when the user taps "Turn on").
 */
export async function enablePush(authToken: string, ask: boolean): Promise<PushResult> {
  if (Platform.OS === 'web') return 'web';
  if (isRunningInExpoGo()) return 'expo-go';

  try {
    if (Platform.OS === 'android') {
      // Must exist BEFORE asking for a token on Android 13+, or no popup appears.
      await Notifications.setNotificationChannelAsync('default', {
        name: 'Default',
        importance: Notifications.AndroidImportance.DEFAULT,
      });
    }

    let perm = await Notifications.getPermissionsAsync();
    if (!perm.granted && ask) perm = await Notifications.requestPermissionsAsync();
    if (!perm.granted) return 'denied';

    const projectId: string | undefined =
      Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
    if (!projectId) return 'no-project-id';

    const { data } = await Notifications.getExpoPushTokenAsync({ projectId });
    await api.setPushToken(authToken, data);
    return 'enabled';
  } catch {
    return 'error';
  }
}

/** Tell the backend to stop sending to this phone. */
export async function disablePush(authToken: string): Promise<void> {
  try {
    await api.clearPushToken(authToken);
  } catch {
    // Not critical: if this fails, the token just stays until it expires.
  }
}

export function pushResultMessage(r: PushResult): string {
  switch (r) {
    case 'enabled':
      return "On. You'll be told about new requests and accepted connections.";
    case 'denied':
      return 'Notifications are not allowed. You can allow them in your phone Settings.';
    case 'expo-go':
      return 'Not available in Expo Go. Push notifications need a development build of the app.';
    case 'web':
      return 'Not available in the web version.';
    case 'no-project-id':
      return 'Missing EAS project id. Run `npx eas-cli@latest init` in src/mobile first.';
    case 'error':
      return "Couldn't turn on notifications. Check your internet and try again.";
  }
}
