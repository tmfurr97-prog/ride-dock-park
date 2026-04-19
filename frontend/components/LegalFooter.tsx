import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, SPACING } from '../constants/theme';

export default function LegalFooter() {
  const router = useRouter();
  return (
    <View style={styles.footer}>
      <Text style={styles.disclaimer}>
        FurrstCamp Travel is a platform provider and does not provide insurance
        or legal representation.
      </Text>
      <View style={styles.linkRow}>
        <TouchableOpacity onPress={() => router.push('/legal/terms')}>
          <Text style={styles.link}>Terms of Service</Text>
        </TouchableOpacity>
        <Text style={styles.separator}>·</Text>
        <TouchableOpacity onPress={() => router.push('/legal/privacy')}>
          <Text style={styles.link}>Privacy Policy</Text>
        </TouchableOpacity>
      </View>
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
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  link: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  separator: {
    fontSize: 12,
    color: COLORS.textLight,
  },
});
