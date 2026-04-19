import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../constants/theme';
import { useAuthStore } from '../store/authStore';
import api from '../services/api';

export default function Verification() {
  const router = useRouter();
  const { user, updateUser } = useAuthStore();
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    setLoading(true);
    try {
      // Get origin URL from env (no hardcoded fallback — each environment provides its own)
      const originUrl = process.env.EXPO_PUBLIC_BACKEND_URL?.replace('/api', '') || '';

      const response = await api.post('/api/payments/verification/create-checkout', {
        origin_url: originUrl,
      });

      // Open Stripe checkout in browser
      const { url } = response.data;
      const supported = await Linking.canOpenURL(url);
      
      if (supported) {
        await Linking.openURL(url);
      } else {
        Alert.alert('Error', 'Cannot open payment page');
      }
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to start verification'
      );
    } finally {
      setLoading(false);
    }
  };

  if (user?.is_verified) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.content}>
          <View style={styles.successIcon}>
            <Ionicons name="checkmark-circle" size={80} color={COLORS.success} />
          </View>
          <Text style={styles.title}>Already Verified!</Text>
          <Text style={styles.subtitle}>
            Your account is verified and ready to use all features.
          </Text>
          <TouchableOpacity
            style={styles.button}
            onPress={() => router.back()}
          >
            <Text style={styles.buttonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Verification</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.replace('/(tabs)')}
        >
          <Ionicons name="home" size={22} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <Ionicons name="shield-checkmark" size={80} color={COLORS.primary} />
        </View>

        <Text style={styles.title}>Get Verified</Text>
        <Text style={styles.subtitle}>
          Complete verification to unlock all features
        </Text>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Verification unlocks:</Text>
          
          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={COLORS.success} />
            <Text style={styles.featureText}>Post RV Rentals, Land Stays & Storage listings</Text>
          </View>

          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={COLORS.success} />
            <Text style={styles.featureText}>Book and reserve listings</Text>
          </View>

          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={COLORS.success} />
            <Text style={styles.featureText}>Contact listing owners</Text>
          </View>

          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={COLORS.success} />
            <Text style={styles.featureText}>Build trust with verified badge</Text>
          </View>
        </View>

        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>One-time fee</Text>
          <Text style={styles.price}>$14.99</Text>
          <Text style={styles.priceNote}>Secure payment via Stripe</Text>
        </View>

        <TouchableOpacity
          style={[styles.verifyButton, loading && styles.buttonDisabled]}
          onPress={handleVerify}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.surface} />
          ) : (
            <>
              <Ionicons name="shield-checkmark" size={20} color={COLORS.surface} />
              <Text style={styles.verifyButtonText}>Verify Now</Text>
            </>
          )}
        </TouchableOpacity>

        <Text style={styles.disclaimer}>
          By proceeding, you'll be redirected to Stripe's secure payment page. 
          Your payment information is never stored on our servers.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerTitle: {
    ...TYPOGRAPHY.h3,
    marginLeft: SPACING.md,
  },
  content: {
    flex: 1,
    padding: SPACING.lg,
  },
  iconContainer: {
    alignItems: 'center',
    marginVertical: SPACING.xl,
  },
  successIcon: {
    alignItems: 'center',
    marginVertical: SPACING.xxl,
  },
  title: {
    ...TYPOGRAPHY.h1,
    textAlign: 'center',
    marginBottom: SPACING.sm,
  },
  subtitle: {
    ...TYPOGRAPHY.body,
    textAlign: 'center',
    color: COLORS.textLight,
    marginBottom: SPACING.xl,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
    ...SHADOWS.medium,
  },
  cardTitle: {
    ...TYPOGRAPHY.h3,
    marginBottom: SPACING.md,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
    marginBottom: SPACING.md,
  },
  featureText: {
    ...TYPOGRAPHY.body,
    flex: 1,
  },
  priceCard: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: SPACING.lg,
    alignItems: 'center',
    marginBottom: SPACING.lg,
    ...SHADOWS.large,
  },
  priceLabel: {
    fontSize: 14,
    color: COLORS.surface,
    opacity: 0.8,
    marginBottom: SPACING.xs,
  },
  price: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.surface,
    marginBottom: SPACING.xs,
  },
  priceNote: {
    fontSize: 14,
    color: COLORS.surface,
    opacity: 0.8,
  },
  verifyButton: {
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    padding: SPACING.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
    minHeight: 48,
    ...SHADOWS.medium,
  },
  button: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.lg,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  verifyButtonText: {
    ...TYPOGRAPHY.button,
    fontSize: 18,
  },
  buttonText: {
    ...TYPOGRAPHY.button,
  },
  disclaimer: {
    ...TYPOGRAPHY.caption,
    textAlign: 'center',
    lineHeight: 18,
  },
});
