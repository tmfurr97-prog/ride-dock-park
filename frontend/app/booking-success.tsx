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
import api from '../services/api';

export default function BookingSuccess() {
  const router = useRouter();
  const { session_id } = useLocalSearchParams();
  const [status, setStatus] = useState<'checking' | 'paid' | 'failed'>('checking');
  const [amount, setAmount] = useState<number | null>(null);

  useEffect(() => {
    let attempts = 0;
    const poll = async () => {
      if (!session_id) return;
      try {
        const res = await api.get(`/api/payments/booking/status/${session_id}`);
        if (res.data.status === 'paid') {
          setStatus('paid');
          setAmount(res.data.amount);
          return;
        }
        if (attempts++ < 10) setTimeout(poll, 2000);
        else setStatus('failed');
      } catch {
        if (attempts++ < 10) setTimeout(poll, 2000);
        else setStatus('failed');
      }
    };
    poll();
  }, [session_id]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {status === 'checking' ? (
          <>
            <ActivityIndicator size="large" color={COLORS.primary} />
            <Text style={styles.title}>Confirming Payment…</Text>
          </>
        ) : status === 'paid' ? (
          <>
            <View style={styles.iconCircle}>
              <Ionicons name="checkmark" size={64} color={COLORS.surface} />
            </View>
            <Text style={styles.title}>Payment Received!</Text>
            {amount !== null ? (
              <Text style={styles.amount}>${amount.toFixed(2)}</Text>
            ) : null}
            <Text style={styles.desc}>
              Your booking is confirmed. The host will review shortly.
              Security deposits are held as a pre-authorization and released
              48 hours after the rental ends if no damages are reported.
            </Text>
          </>
        ) : (
          <>
            <Ionicons name="alert-circle" size={64} color={COLORS.error} />
            <Text style={styles.title}>Payment Not Received</Text>
            <Text style={styles.desc}>
              We couldn't confirm your payment. Please check your bookings or
              try again.
            </Text>
          </>
        )}
        <TouchableOpacity
          style={styles.btn}
          onPress={() => router.replace('/(tabs)/bookings')}
        >
          <Text style={styles.btnText}>Go to Bookings</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: SPACING.xl, gap: SPACING.md },
  iconCircle: { width: 100, height: 100, borderRadius: 50, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center' },
  title: { ...TYPOGRAPHY.h1, textAlign: 'center', color: COLORS.text },
  amount: { fontSize: 32, fontWeight: 'bold', color: COLORS.primary },
  desc: { ...TYPOGRAPHY.body, textAlign: 'center', color: COLORS.textLight, lineHeight: 22 },
  btn: { backgroundColor: COLORS.primary, paddingHorizontal: SPACING.xl, paddingVertical: SPACING.md, borderRadius: 10, marginTop: SPACING.md },
  btnText: { ...TYPOGRAPHY.button },
});
