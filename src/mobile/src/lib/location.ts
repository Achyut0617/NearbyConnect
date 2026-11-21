// GPS helpers. FOREGROUND ONLY: we never ask for background location.
// Privacy: coordinates are kept in memory only, never saved on the device.
import * as Location from 'expo-location';

export type PermissionState = 'granted' | 'denied' | 'undetermined';

export type Coords = { lat: number; lon: number };

/** Check the current permission without showing a popup. */
export async function getPermission(): Promise<PermissionState> {
  const res = await Location.getForegroundPermissionsAsync();
  return res.status as PermissionState;
}

/** Show the system "Allow location?" popup. Returns true if allowed. */
export async function requestPermission(): Promise<boolean> {
  const res = await Location.requestForegroundPermissionsAsync();
  return res.status === 'granted';
}

/** Get the phone's current position. Throws if permission is missing. */
export async function getCurrentCoords(): Promise<Coords> {
  const pos = await Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.Balanced, // good enough for "nearby", saves battery
  });
  return { lat: pos.coords.latitude, lon: pos.coords.longitude };
}
