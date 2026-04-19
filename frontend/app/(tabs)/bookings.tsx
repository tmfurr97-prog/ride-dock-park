import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY } from '../../constants/theme';
import api from '../../services/api';
import LegalFooter from '../../components/LegalFooter';
import { confirm } from '../../utils/dialog';

export default function Bookings() {
  const [guestBookings, setGuestBookings] = useState<any[]>([]);
  const [hostBookings, setHostBookings] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'guest' | 'host'>('guest');

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      const [guestRes, hostRes] = await Promise.all([
        api.get('/api/bookings/guest'),
        api.get('/api/bookings/host'),
      ]);
      setGuestBookings(guestRes.data);
      setHostBookings(hostRes.data);
    } catch (error) {
      console.error('Failed to load bookings:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleAcceptInsurance = async (bookingId: string) => {
    try {
      await api.patch(`/api/bookings/${bookingId}/accept-insurance`);
      Alert.alert('Accepted', 'Insurance approved — booking confirmed.');
      loadBookings();
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.detail || 'Failed to accept');
    }
  };

  const handleApprove = async (bookingId: string) => {
    try {
      await api.patch(`/api/bookings/${bookingId}/approve`);
      Alert.alert('Approved', 'Booking confirmed!');
      loadBookings();
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.detail || 'Failed to approve');
    }
  };

  const handleDecline = async (bookingId: string) => {
    const ok = await confirm(
      'Decline Booking?',
      'This will cancel the request. The guest will be notified.',
      'Decline',
      'Cancel',
      true
    );
    if (!ok) return;
    try {
      await api.patch(`/api/bookings/${bookingId}/decline`);
      Alert.alert('Declined', 'Booking cancelled.');
      loadBookings();
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.detail || 'Failed');
    }
  };

  const handleRejectInsurance = async (bookingId: string) => {
    const ok = await confirm(
      'Reject Insurance?',
      'This will cancel the booking. The guest will be notified.',
      'Reject',
      'Cancel',
      true
    );
    if (!ok) return;
    try {
      await api.patch(`/api/bookings/${bookingId}/reject-insurance`);
      Alert.alert('Rejected', 'Booking cancelled.');
      loadBookings();
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.detail || 'Failed');
    }
  };

  const renderBookingCard = ({ item }: any) => {
    const isHostTab = activeTab === 'host';
    const needsInsurance =
      isHostTab && item.status === 'awaiting_insurance_review';
    const needsApproval =
      isHostTab && item.status === 'awaiting_host_approval';
    return (
      <View style={styles.card}>
        <Text style={styles.cardTitle}>{item.listing_title || 'Listing'}</Text>
        {item.guest_name && isHostTab && (
          <View style={styles.cardRow}>
            <Ionicons name="person" size={16} color={COLORS.textLight} />
            <Text style={styles.cardText}>{item.guest_name}</Text>
          </View>
        )}
        <View style={styles.cardRow}>
          <Ionicons name="calendar" size={16} color={COLORS.textLight} />
          <Text style={styles.cardText}>
            {new Date(item.start_date).toLocaleDateString()} -{' '}
            {new Date(item.end_date).toLocaleDateString()}
          </Text>
        </View>
        <View style={styles.cardRow}>
          <Ionicons name="cash" size={16} color={COLORS.textLight} />
          <Text style={styles.cardText}>${item.total_price}</Text>
        </View>
        <View
          style={[
            styles.statusBadge,
            (item.status === 'awaiting_insurance_review' ||
              item.status === 'awaiting_host_approval') && styles.statusWarn,
            item.status === 'confirmed' && styles.statusOk,
            item.status === 'cancelled' && styles.statusErr,
          ]}
        >
          <Text style={styles.statusText}>
            {item.status.replace(/_/g, ' ')}
          </Text>
        </View>

        {needsInsurance && (
          <View style={styles.insuranceBox}>
            <View style={styles.insuranceHeader}>
              <Ionicons
                name="shield-checkmark"
                size={20}
                color={COLORS.primary}
              />
              <Text style={styles.insuranceTitle}>Insurance Review Required</Text>
            </View>
            <Text style={styles.insuranceHelp}>
              Review your listing's insurance documentation and approve this
              booking to confirm it.
            </Text>
            <View style={styles.insuranceBtnRow}>
              <TouchableOpacity
                style={[styles.insuranceBtn, styles.insuranceReject]}
                onPress={() => handleRejectInsurance(item.id)}
              >
                <Text style={styles.insuranceRejectTxt}>Reject</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.insuranceBtn, styles.insuranceAccept]}
                onPress={() => handleAcceptInsurance(item.id)}
              >
                <Text style={styles.insuranceAcceptTxt}>Accept & Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {needsApproval && (
          <View style={styles.insuranceBox}>
            <View style={styles.insuranceHeader}>
              <Ionicons name="hand-left" size={20} color={COLORS.primary} />
              <Text style={styles.insuranceTitle}>New Booking Request</Text>
            </View>
            <Text style={styles.insuranceHelp}>
              Review this request and decide whether to accept. The guest has
              agreed to your house rules.
            </Text>
            <View style={styles.insuranceBtnRow}>
              <TouchableOpacity
                style={[styles.insuranceBtn, styles.insuranceReject]}
                onPress={() => handleDecline(item.id)}
              >
                <Text style={styles.insuranceRejectTxt}>Decline</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.insuranceBtn, styles.insuranceAccept]}
                onPress={() => handleApprove(item.id)}
              >
                <Text style={styles.insuranceAcceptTxt}>Approve</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
    );
  };

  const bookings = activeTab === 'guest' ? guestBookings : hostBookings;

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.tabs}>
        <Text
          style={[styles.tab, activeTab === 'guest' && styles.tabActive]}
          onPress={() => setActiveTab('guest')}
        >
          My Bookings
        </Text>
        <Text
          style={[styles.tab, activeTab === 'host' && styles.tabActive]}
          onPress={() => setActiveTab('host')}
        >
          Hosting
        </Text>
      </View>

      <FlatList
        data={bookings}
        renderItem={renderBookingCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              loadBookings();
            }}
            tintColor={COLORS.primary}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons
              name="calendar-outline"
              size={64}
              color={COLORS.textLight}
            />
            <Text style={styles.emptyText}>No bookings yet</Text>
          </View>
        }
      />
      <LegalFooter />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  tab: {
    flex: 1,
    padding: SPACING.md,
    textAlign: 'center',
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textLight,
  },
  tabActive: {
    color: COLORS.primary,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.primary,
  },
  listContent: {
    padding: SPACING.md,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.md,
  },
  cardTitle: {
    ...TYPOGRAPHY.h3,
    marginBottom: SPACING.sm,
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.xs,
  },
  cardText: {
    ...TYPOGRAPHY.caption,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.accent,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 4,
    marginTop: SPACING.sm,
  },
  statusWarn: {
    backgroundColor: '#C8860D',
  },
  statusOk: {
    backgroundColor: COLORS.primary,
  },
  statusErr: {
    backgroundColor: '#8B2E2E',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.surface,
    textTransform: 'capitalize',
  },
  insuranceBox: {
    marginTop: SPACING.md,
    padding: SPACING.md,
    backgroundColor: '#F0F7F0',
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
    borderRadius: 6,
  },
  insuranceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.xs,
  },
  insuranceTitle: {
    fontWeight: '700',
    fontSize: 14,
    color: COLORS.primary,
  },
  insuranceHelp: {
    fontSize: 12,
    lineHeight: 16,
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  insuranceBtnRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  insuranceBtn: {
    flex: 1,
    paddingVertical: SPACING.sm,
    borderRadius: 6,
    alignItems: 'center',
  },
  insuranceAccept: {
    backgroundColor: COLORS.primary,
  },
  insuranceReject: {
    borderWidth: 1,
    borderColor: '#8B2E2E',
    backgroundColor: COLORS.surface,
  },
  insuranceAcceptTxt: {
    color: COLORS.surface,
    fontWeight: '700',
    fontSize: 14,
  },
  insuranceRejectTxt: {
    color: '#8B2E2E',
    fontWeight: '700',
    fontSize: 14,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xxl * 2,
  },
  emptyText: {
    ...TYPOGRAPHY.h3,
    marginTop: SPACING.md,
  },
});