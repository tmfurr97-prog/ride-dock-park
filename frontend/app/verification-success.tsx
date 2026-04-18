import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY } from '../constants/theme';
import { useAuthStore } from '../store/authStore';
import api from '../services/api';

export default function VerificationSuccess() {
  const router = useRouter();
  const { session_id } = useLocalSearchParams();
  const { user, updateUser } = useAuthStore();
  const [status, setStatus] = useState<'checking' | 'success' | 'failed'>('checking');
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    if (session_id) {
      checkPaymentStatus();
    }
  }, [session_id]);

  const checkPaymentStatus = async () => {
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    if (attempts >= maxAttempts) {
      setStatus('failed');
      return;
    }

    try {
      const response = await api.get(`/api/payments/verification/status/${session_id}`);
      
      if (response.data.payment_status === 'paid') {
        setStatus('success');
        
        // Update user in store
        if (user) {
          updateUser({ ...user, is_verified: true });
        }
      } else if (response.data.status === 'expired') {
        setStatus('failed');
      } else {
        // Continue polling
        setAttempts(attempts + 1);
        setTimeout(checkPaymentStatus, pollInterval);
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
      setAttempts(attempts + 1);
      setTimeout(checkPaymentStatus, pollInterval);
    }
  };

  const renderContent = () => {
    switch (status) {
      case 'checking':
        return (
          <View style={styles.content}>
            <ActivityIndicator size="large" color={COLORS.primary} />
            <Text style={styles.title}>Processing Payment...</Text>
            <Text style={styles.subtitle}>
              Please wait while we confirm your payment
            </Text>
          </View>
        );

      case 'success':
        return (
          <View style={styles.content}>
            <View style={styles.successIcon}>
              <Ionicons name="checkmark-circle" size={100} color={COLORS.success} />
            </View>
            <Text style={styles.title}>Verification Complete!</Text>
            <Text style={styles.subtitle}>
              Your account is now verified. You can now create listings and book properties.
            </Text>
            <TouchableOpacity
              style={styles.button}
              onPress={() => router.replace('/(tabs)')}
            >
              <Text style={styles.buttonText}>Continue</Text>
            </TouchableOpacity>
          </View>
        );

      case 'failed':
        return (
          <View style={styles.content}>
            <View style={styles.errorIcon}>
              <Ionicons name="close-circle" size={100} color={COLORS.error} />
            </View>
            <Text style={styles.title}>Payment Issue</Text>
            <Text style={styles.subtitle}>
              We couldn't verify your payment. Please try again or contact support.
            </Text>
            <TouchableOpacity
              style={styles.button}
              onPress={() => router.replace('/verification')}
            >
              <Text style={styles.buttonText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {renderContent()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.lg,
  },
  successIcon: {
    marginBottom: SPACING.xl,
  },
  errorIcon: {
    marginBottom: SPACING.xl,
  },
  title: {
    ...TYPOGRAPHY.h1,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  subtitle: {
    ...TYPOGRAPHY.body,
    textAlign: 'center',
    color: COLORS.textLight,
    marginBottom: SPACING.xl,
  },
  button: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    minWidth: 200,
    alignItems: 'center',
  },
  buttonText: {
    ...TYPOGRAPHY.button,
  },
});
