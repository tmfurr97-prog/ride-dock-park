import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  Alert,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../constants/theme';
import api from '../services/api';

export default function MyListings() {
  const router = useRouter();
  const [listings, setListings] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadListings();
  }, []);

  const loadListings = async () => {
    try {
      const response = await api.get('/api/listings/user/me');
      setListings(response.data);
    } catch (error) {
      console.error('Failed to load listings:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleDelete = (listingId: string, title: string) => {
    Alert.alert(
      'Delete Listing',
      `Are you sure you want to delete "${title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/api/listings/${listingId}`);
              Alert.alert('Success', 'Listing deleted');
              loadListings();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete listing');
            }
          },
        },
      ]
    );
  };

  const renderListingCard = ({ item }: any) => (
    <View style={styles.card}>
      <TouchableOpacity
        style={styles.cardContent}
        onPress={() => router.push(`/listing/${item.id}`)}
      >
        {item.images && item.images.length > 0 ? (
          <Image
            source={{ uri: item.images[0] }}
            style={styles.cardImage}
            resizeMode="cover"
          />
        ) : (
          <View style={[styles.cardImage, styles.placeholderImage]}>
            <Ionicons name="image-outline" size={40} color={COLORS.textLight} />
          </View>
        )}
        <View style={styles.cardInfo}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.cardLocation} numberOfLines={1}>
            <Ionicons name="location" size={14} color={COLORS.textLight} />
            {' '}{item.location}
          </Text>
          <View style={styles.cardFooter}>
            <Text style={styles.cardPrice}>${item.price}</Text>
            <View style={[
              styles.statusBadge,
              item.status === 'active' ? styles.statusActive : styles.statusInactive
            ]}>
              <Text style={styles.statusText}>{item.status}</Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
      <TouchableOpacity
        style={styles.deleteButton}
        onPress={() => handleDelete(item.id, item.title)}
      >
        <Ionicons name="trash" size={20} color={COLORS.error} />
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.surface} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>My Listings</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => router.push('/create-listing')}
        >
          <Ionicons name="add" size={24} color={COLORS.surface} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={listings}
        renderItem={renderListingCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              loadListings();
            }}
            tintColor={COLORS.primary}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="folder-open-outline" size={64} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No listings yet</Text>
            <TouchableOpacity
              style={styles.createButton}
              onPress={() => router.push('/create-listing')}
            >
              <Text style={styles.createButtonText}>Create Your First Listing</Text>
            </TouchableOpacity>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: SPACING.md,
    backgroundColor: COLORS.primary,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerTitle: {
    ...TYPOGRAPHY.h3,
    color: COLORS.surface,
  },
  addButton: {
    padding: SPACING.sm,
  },
  listContent: {
    padding: SPACING.md,
  },
  card: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    marginBottom: SPACING.md,
    overflow: 'hidden',
    ...SHADOWS.medium,
  },
  cardContent: {
    flex: 1,
    flexDirection: 'row',
  },
  cardImage: {
    width: 100,
    height: 100,
    backgroundColor: COLORS.background,
  },
  placeholderImage: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardInfo: {
    flex: 1,
    padding: SPACING.md,
  },
  cardTitle: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    marginBottom: SPACING.xs,
  },
  cardLocation: {
    ...TYPOGRAPHY.caption,
    marginBottom: SPACING.sm,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  statusBadge: {
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 4,
  },
  statusActive: {
    backgroundColor: COLORS.success,
  },
  statusInactive: {
    backgroundColor: COLORS.textLight,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.surface,
    textTransform: 'capitalize',
  },
  deleteButton: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.background,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xxl * 2,
  },
  emptyText: {
    ...TYPOGRAPHY.h3,
    marginTop: SPACING.md,
    marginBottom: SPACING.lg,
  },
  createButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
  },
  createButtonText: {
    ...TYPOGRAPHY.button,
  },
});