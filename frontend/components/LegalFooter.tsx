import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SPACING } from '../constants/theme';

export default function LegalFooter() {
  const router = useRouter();
  return (
    <View style={styles.footer}>
      <Text style={styles.disclaimer}>
        DriveShare & Dock is a platform provider and does not provide insurance
        or legal representation.
      </Text>
      <TouchableOpacity onPress={() => router.push('/legal/terms')}>
        <Text style={styles.link}>Terms of Service</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  footer: {
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    alignItems: 'center',
    gap: SPACING.xs,
  },
  disclaimer: {
    fontSize: 11,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 16,
  },
  link: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
