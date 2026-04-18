import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY } from '../../constants/theme';
import api from '../../services/api';

export default function Bookings() {
  const [guestBookings, setGuestBookings] = useState([]);
  const [hostBookings, setHostBookings] = useState([]);
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

  const renderBookingCard = ({ item }: any) => (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{item.listing_title || 'Listing'}</Text>
      <View style={styles.cardRow}>
        <Ionicons name="calendar" size={16} color={COLORS.textLight} />
        <Text style={styles.cardText}>
          {new Date(item.start_date).toLocaleDateString()} - {new Date(item.end_date).toLocaleDateString()}
        </Text>
      </View>
      <View style={styles.cardRow}>
        <Ionicons name="cash" size={16} color={COLORS.textLight} />
        <Text style={styles.cardText}>${item.total_price}</Text>
      </View>
      <View style={styles.statusBadge}>
        <Text style={styles.statusText}>{item.status}</Text>
      </View>
    </View>
  );

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
            <Ionicons name="calendar-outline" size={64} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No bookings yet</Text>
          </View>
        }
      />
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
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.surface,
    textTransform: 'capitalize',
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