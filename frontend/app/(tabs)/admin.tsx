import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../../constants/theme';
import api from '../../services/api';
import { confirm } from '../../utils/dialog';

export default function AdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [listings, setListings] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'stats' | 'users' | 'listings' | 'payments'>('stats');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, usersRes, listingsRes, paymentsRes] = await Promise.all([
        api.get('/api/admin/stats'),
        api.get('/api/admin/users?limit=10'),
        api.get('/api/admin/listings?limit=10'),
        api.get('/api/admin/payments?limit=10'),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data.users);
      setListings(listingsRes.data.listings);
      setPayments(paymentsRes.data.payments);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleVerifyUser = async (userId: string, userName: string) => {
    try {
      await api.patch(`/api/admin/users/${userId}/verify`);
      Alert.alert('Success', `${userName} has been verified`);
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to verify user');
    }
  };

  const handleBanUser = async (userId: string, userName: string, currentlyBanned: boolean) => {
    const ok = await confirm(
      currentlyBanned ? 'Unban User' : 'Ban User',
      `Are you sure you want to ${currentlyBanned ? 'unban' : 'ban'} ${userName}?`,
      currentlyBanned ? 'Unban' : 'Ban',
      'Cancel',
      !currentlyBanned
    );
    if (!ok) return;
    try {
      await api.patch(`/api/admin/users/${userId}/ban`, { banned: !currentlyBanned });
      Alert.alert('Success', `User ${currentlyBanned ? 'unbanned' : 'banned'}`);
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to update user');
    }
  };

  const handleDeleteListing = async (listingId: string, title: string) => {
    const ok = await confirm('Delete Listing', `Delete "${title}"?`, 'Delete', 'Cancel', true);
    if (!ok) return;
    try {
      await api.delete(`/api/admin/listings/${listingId}`);
      Alert.alert('Success', 'Listing deleted');
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to delete listing');
    }
  };

  const renderStats = () => (
    <View style={styles.statsContainer}>
      <View style={styles.statCard}>
        <Ionicons name="people" size={32} color={COLORS.primary} />
        <Text style={styles.statValue}>{stats?.total_users || 0}</Text>
        <Text style={styles.statLabel}>Total Users</Text>
      </View>
      <View style={styles.statCard}>
        <Ionicons name="checkmark-circle" size={32} color={COLORS.success} />
        <Text style={styles.statValue}>{stats?.verified_users || 0}</Text>
        <Text style={styles.statLabel}>Verified</Text>
      </View>
      <View style={styles.statCard}>
        <Ionicons name="list" size={32} color={COLORS.accent} />
        <Text style={styles.statValue}>{stats?.total_listings || 0}</Text>
        <Text style={styles.statLabel}>Listings</Text>
      </View>
      <View style={styles.statCard}>
        <Ionicons name="calendar" size={32} color={COLORS.secondary} />
        <Text style={styles.statValue}>{stats?.total_bookings || 0}</Text>
        <Text style={styles.statLabel}>Bookings</Text>
      </View>
      <View style={[styles.statCard, styles.statCardWide]}>
        <Ionicons name="cash" size={32} color={COLORS.primary} />
        <Text style={styles.statValue}>${stats?.total_revenue?.toFixed(2) || '0.00'}</Text>
        <Text style={styles.statLabel}>Total Revenue</Text>
      </View>
      <View style={[styles.statCard, styles.statCardWide]}>
        <Ionicons name="trending-up" size={32} color={COLORS.accent} />
        <Text style={styles.statValue}>{stats?.recent_users || 0}</Text>
        <Text style={styles.statLabel}>New (7 days)</Text>
      </View>
    </View>
  );

  const renderUsers = () => (
    <View>
      {users.map((user) => (
        <View key={user.id} style={styles.listItem}>
          <View style={styles.listItemInfo}>
            <Text style={styles.listItemTitle}>{user.name}</Text>
            <Text style={styles.listItemSubtitle}>{user.email}</Text>
            <View style={styles.badges}>
              {user.is_verified && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>Verified</Text>
                </View>
              )}
              {user.is_admin && (
                <View style={[styles.badge, styles.badgeAdmin]}>
                  <Text style={styles.badgeText}>Admin</Text>
                </View>
              )}
              {user.is_banned && (
                <View style={[styles.badge, styles.badgeBanned]}>
                  <Text style={styles.badgeText}>Banned</Text>
                </View>
              )}
            </View>
          </View>
          <View style={styles.listItemActions}>
            {!user.is_verified && (
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => handleVerifyUser(user.id, user.name)}
              >
                <Ionicons name="checkmark" size={20} color={COLORS.success} />
              </TouchableOpacity>
            )}
            {!user.is_admin && (
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => handleBanUser(user.id, user.name, user.is_banned)}
              >
                <Ionicons
                  name={user.is_banned ? "lock-open" : "ban"}
                  size={20}
                  color={COLORS.error}
                />
              </TouchableOpacity>
            )}
          </View>
        </View>
      ))}
    </View>
  );

  const renderListings = () => (
    <View>
      {listings.map((listing) => (
        <View key={listing.id} style={styles.listItem}>
          <View style={styles.listItemInfo}>
            <Text style={styles.listItemTitle}>{listing.title}</Text>
            <Text style={styles.listItemSubtitle}>
              {listing.owner_name} • ${listing.price}
            </Text>
            <Text style={styles.listItemSubtitle}>{listing.category}</Text>
          </View>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => handleDeleteListing(listing.id, listing.title)}
          >
            <Ionicons name="trash" size={20} color={COLORS.error} />
          </TouchableOpacity>
        </View>
      ))}
    </View>
  );

  const renderPayments = () => (
    <View>
      {payments.map((payment) => (
        <View key={payment.id} style={styles.listItem}>
          <View style={styles.listItemInfo}>
            <Text style={styles.listItemTitle}>${payment.amount}</Text>
            <Text style={styles.listItemSubtitle}>
              {payment.email} • {payment.type}
            </Text>
            <Text style={styles.listItemSubtitle}>
              {new Date(payment.created_at).toLocaleDateString()}
            </Text>
          </View>
          <View style={[
            styles.statusBadge,
            payment.payment_status === 'paid' ? styles.statusPaid : styles.statusPending
          ]}>
            <Text style={styles.statusText}>{payment.payment_status}</Text>
          </View>
        </View>
      ))}
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'stats' && styles.tabActive]}
          onPress={() => setActiveTab('stats')}
        >
          <Text style={[styles.tabText, activeTab === 'stats' && styles.tabTextActive]}>
            Dashboard
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'users' && styles.tabActive]}
          onPress={() => setActiveTab('users')}
        >
          <Text style={[styles.tabText, activeTab === 'users' && styles.tabTextActive]}>
            Users
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'listings' && styles.tabActive]}
          onPress={() => setActiveTab('listings')}
        >
          <Text style={[styles.tabText, activeTab === 'listings' && styles.tabTextActive]}>
            Listings
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'payments' && styles.tabActive]}
          onPress={() => setActiveTab('payments')}
        >
          <Text style={[styles.tabText, activeTab === 'payments' && styles.tabTextActive]}>
            Payments
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              loadData();
            }}
            tintColor={COLORS.primary}
          />
        }
      >
        {activeTab === 'stats' && renderStats()}
        {activeTab === 'users' && renderUsers()}
        {activeTab === 'listings' && renderListings()}
        {activeTab === 'payments' && renderPayments()}
      </ScrollView>
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
    alignItems: 'center',
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: COLORS.primary,
  },
  tabText: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  tabTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  content: {
    padding: SPACING.md,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.md,
  },
  statCard: {
    width: '48%',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.lg,
    alignItems: 'center',
    ...SHADOWS.medium,
  },
  statCardWide: {
    width: '48%',
  },
  statValue: {
    ...TYPOGRAPHY.h1,
    fontSize: 32,
    marginTop: SPACING.sm,
    color: COLORS.primary,
  },
  statLabel: {
    ...TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
  },
  listItem: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    alignItems: 'center',
    ...SHADOWS.small,
  },
  listItemInfo: {
    flex: 1,
  },
  listItemTitle: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    marginBottom: SPACING.xs,
  },
  listItemSubtitle: {
    ...TYPOGRAPHY.caption,
    marginBottom: SPACING.xs,
  },
  listItemActions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  actionButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badges: {
    flexDirection: 'row',
    gap: SPACING.xs,
    marginTop: SPACING.xs,
  },
  badge: {
    backgroundColor: COLORS.success,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 4,
  },
  badgeAdmin: {
    backgroundColor: COLORS.primary,
  },
  badgeBanned: {
    backgroundColor: COLORS.error,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.surface,
  },
  statusBadge: {
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 4,
  },
  statusPaid: {
    backgroundColor: COLORS.success,
  },
  statusPending: {
    backgroundColor: COLORS.textLight,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.surface,
    textTransform: 'capitalize',
  },
});
