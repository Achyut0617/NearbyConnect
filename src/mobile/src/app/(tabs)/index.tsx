// Feed tab. Filled in at Step 12.
import { View } from 'react-native';

import { space } from '../../lib/theme';
import { Muted } from '../../lib/ui';

export default function FeedScreen() {
  return (
    <View style={{ padding: space.xl }}>
      <Muted>Nearby places will appear here (Step 12).</Muted>
    </View>
  );
}
