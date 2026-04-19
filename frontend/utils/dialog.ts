import { Alert, Platform } from 'react-native';

/**
 * Cross-platform confirmation dialog.
 * On React Native Web, Alert.alert callbacks don't fire reliably, so we fall
 * back to the browser's native window.confirm().
 *
 * Usage:
 *   const ok = await confirm('Logout', 'Are you sure you want to logout?');
 *   if (ok) doLogout();
 */
export function confirm(
  title: string,
  message?: string,
  confirmLabel = 'OK',
  cancelLabel = 'Cancel',
  destructive = false
): Promise<boolean> {
  return new Promise((resolve) => {
    if (Platform.OS === 'web') {
      if (typeof window !== 'undefined') {
        const body = message ? `${title}\n\n${message}` : title;
        resolve(window.confirm(body));
      } else {
        resolve(false);
      }
      return;
    }

    Alert.alert(
      title,
      message,
      [
        { text: cancelLabel, style: 'cancel', onPress: () => resolve(false) },
        {
          text: confirmLabel,
          style: destructive ? 'destructive' : 'default',
          onPress: () => resolve(true),
        },
      ],
      { cancelable: true, onDismiss: () => resolve(false) }
    );
  });
}

/**
 * Cross-platform notice (no action, just OK).
 */
export function notify(title: string, message?: string): Promise<void> {
  return new Promise((resolve) => {
    if (Platform.OS === 'web') {
      if (typeof window !== 'undefined') {
        window.alert(message ? `${title}\n\n${message}` : title);
      }
      resolve();
      return;
    }
    Alert.alert(title, message, [{ text: 'OK', onPress: () => resolve() }]);
  });
}
