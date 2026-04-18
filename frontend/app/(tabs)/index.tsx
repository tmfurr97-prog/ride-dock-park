import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Image,
  Alert,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../../constants/theme';
import { useAuthStore } from '../../store/authStore';
import api from '../../services/api';
import LegalFooter from '../../components/LegalFooter';

const CATEGORIES = [
  { id: 'all', label: 'All', icon: 'apps' },
  { id: 'rv_rental', label: 'RV Rentals', icon: 'car' },
  { id: 'land_stay', label: 'Land Stays', icon: 'home' },
  { id: 'vehicle_storage', label: 'Storage', icon: 'cube' },
  { id: 'boat_rental', label: 'Boats', icon: 'boat' },
];

export default function Browse() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadListings();
  }, [selectedCategory]);

  const loadListings = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      if (searchQuery) {
        params.search = searchQuery;
      }

      const response = await api.get('/api/listings', { params });
      setListings(response.data);
    } catch (error) {
      console.error('Failed to load listings:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleSearch = () => {
    loadListings();
  };

  const handleCreateListing = () => {
    if (!user?.is_verified) {
      Alert.alert(
        'Verification Required',
        'You must complete the $25 verification to create listings.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Verify Now', onPress: () => router.push('/verification') },
        ]
      );
      return;
    }
    router.push('/create-listing');
  };

  const renderListingCard = ({ item }: any) => {
    const priceUnit = item.category === 'rv_rental' || item.category === 'boat_rental' ? 'day' : item.category === 'land_stay' ? 'night' : 'month';
    const isBooked = item.status === 'booked';
    const isLongTerm = item.is_long_term || false;

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/listing/${item.id}`)}
      >
        <View style={styles.imageContainer}>
          {item.images && item.images.length > 0 ? (
            <Image
              source={{ uri: item.images[0] }}
              style={styles.cardImage}
              resizeMode="cover"
            />
          ) : (
            <View style={[styles.cardImage, styles.placeholderImage]}>
              <Ionicons name="image-outline" size={48} color={COLORS.textLight} />
            </View>
          )}
          {isBooked && (
            <View style={styles.bookedOverlay}>
              <View style={styles.bookedBadge}>
                <Ionicons name="checkmark-circle" size={16} color={COLORS.surface} />
                <Text style={styles.bookedText}>Currently Booked</Text>
              </View>
            </View>
          )}
          {isLongTerm && (
            <View style={styles.longTermBadge}>
              <Text style={styles.longTermText}>365-Day Lease</Text>
            </View>
          )}
        </View>
        <View style={styles.cardContent}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={styles.cardLocation} numberOfLines={1}>
            <Ionicons name="location" size={14} color={COLORS.textLight} />
            {' '}{item.location}
          </Text>
          <View style={styles.cardFooter}>
            <Text style={styles.cardPrice}>${item.price}/{priceUnit}</Text>
            <View style={styles.categoryBadge}>
              <Text style={styles.categoryBadgeText}>
                {item.category === 'rv_rental' ? 'RV' : item.category === 'land_stay' ? 'Land' : item.category === 'boat_rental' ? 'Boat' : 'Storage'}
              </Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        stickyHeaderIndices={[]}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 0 }}
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
      >
        {/* HERO BANNER */}
        <View style={styles.hero}>
          <View style={styles.heroTopRow}>
            <View>
              <Text style={styles.heroBrand}>DriveShare & Dock</Text>
              <Text style={styles.heroTagline}>
                Where your adventure begins
              </Text>
            </View>
            <TouchableOpacity style={styles.createIconBtn} onPress={handleCreateListing}>
              <Ionicons name="add-circle" size={32} color={COLORS.coral} />
            </TouchableOpacity>
          </View>
          <Text style={styles.heroHeadline}>
            RVs, land, storage & boats.{'\n'}All in one place.
          </Text>
        </View>

        {/* SEARCH CARD (overlaps hero) */}
        <View style={styles.searchCardWrap}>
          <View style={styles.searchCard}>
            <View style={styles.searchRow}>
              <Ionicons name="search" size={20} color={COLORS.textLight} />
              <TextInput
                style={styles.searchInputBig}
                placeholder="Where to? (e.g., Lake of the Ozarks)"
                placeholderTextColor={COLORS.textLight}
                value={searchQuery}
                onChangeText={setSearchQuery}
                onSubmitEditing={handleSearch}
                returnKeyType="search"
              />
            </View>
            <View style={styles.searchDivider} />
            <View style={styles.searchMetaRow}>
              <View style={styles.searchMetaItem}>
                <Ionicons name="calendar-outline" size={16} color={COLORS.textLight} />
                <Text style={styles.searchMetaText}>Any dates</Text>
              </View>
              <View style={styles.searchMetaDot} />
              <View style={styles.searchMetaItem}>
                <Ionicons name="people-outline" size={16} color={COLORS.textLight} />
                <Text style={styles.searchMetaText}>Add guests</Text>
              </View>
            </View>
            <TouchableOpacity style={styles.searchBtn} onPress={handleSearch}>
              <Ionicons name="search" size={18} color={COLORS.surface} />
              <Text style={styles.searchBtnText}>Search</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* CATEGORY CHIPS */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.categoryScroll}
          contentContainerStyle={styles.categoryContainer}
        >
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.id}
              style={[
                styles.categoryChip,
                selectedCategory === cat.id && styles.categoryChipActive,
              ]}
              onPress={() => setSelectedCategory(cat.id)}
            >
              <Ionicons
                name={cat.icon as any}
                size={18}
                color={selectedCategory === cat.id ? COLORS.surface : COLORS.primary}
              />
              <Text
                style={[
                  styles.categoryText,
                  selectedCategory === cat.id && styles.categoryTextActive,
                ]}
              >
                {cat.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* SECTION HEADING */}
        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>Favorites nearby</Text>
          <Text style={styles.sectionSubtitle}>
            Hand-picked spots trusted by travelers
          </Text>
        </View>

        {/* LISTINGS GRID (inline, not FlatList since we're inside ScrollView) */}
        {listings.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="folder-open-outline" size={64} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No listings found</Text>
            <Text style={styles.emptySubtext}>Try a different search or category</Text>
          </View>
        ) : (
          <View style={styles.listContent}>
            {listings.map((item: any) => (
              <View key={item.id}>{renderListingCard({ item })}</View>
            ))}
          </View>
        )}
      </ScrollView>
      <LegalFooter />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  hero: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.lg,
    paddingBottom: SPACING.xxl + SPACING.md, // extra room for search card overlap
  },
  heroTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  heroBrand: {
    fontSize: 22,
    fontWeight: 'bold',
    color: COLORS.surface,
    letterSpacing: 0.3,
  },
  heroTagline: {
    fontSize: 13,
    color: '#B7E4C7',
    marginTop: 2,
  },
  createIconBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.12)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroHeadline: {
    fontSize: 28,
    fontWeight: '800',
    color: COLORS.surface,
    lineHeight: 34,
    marginTop: SPACING.sm,
  },
  searchCardWrap: {
    marginTop: -SPACING.xl - 4,
    paddingHorizontal: SPACING.md,
  },
  searchCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: SPACING.md,
    gap: SPACING.sm,
    ...SHADOWS.medium,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  searchInputBig: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
    paddingVertical: SPACING.sm,
  },
  searchDivider: {
    height: 1,
    backgroundColor: COLORS.border,
  },
  searchMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    paddingVertical: SPACING.xs,
  },
  searchMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    flex: 1,
  },
  searchMetaDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: COLORS.border,
  },
  searchMetaText: {
    fontSize: 14,
    color: COLORS.textLight,
    fontWeight: '500',
  },
  searchBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
    backgroundColor: COLORS.coral,
    paddingVertical: SPACING.md,
    borderRadius: 10,
    marginTop: SPACING.xs,
  },
  searchBtnText: {
    color: COLORS.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  sectionHead: {
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.lg,
    paddingBottom: SPACING.sm,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.text,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  categoryScroll: {
    backgroundColor: 'transparent',
    marginTop: SPACING.md,
  },
  categoryContainer: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    gap: SPACING.sm,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.primary,
    gap: SPACING.xs,
  },
  categoryChipActive: {
    backgroundColor: COLORS.primary,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
  },
  categoryTextActive: {
    color: COLORS.surface,
  },
  listContent: {
    padding: SPACING.md,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    marginBottom: SPACING.md,
    overflow: 'hidden',
    ...SHADOWS.medium,
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
  },
  cardImage: {
    width: '100%',
    height: 200,
    backgroundColor: COLORS.background,
  },
  bookedOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  bookedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    backgroundColor: COLORS.coral,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: 20,
  },
  bookedText: {
    color: COLORS.surface,
    fontSize: 14,
    fontWeight: 'bold',
  },
  longTermBadge: {
    position: 'absolute',
    top: SPACING.sm,
    right: SPACING.sm,
    backgroundColor: COLORS.accent,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 4,
  },
  longTermText: {
    color: COLORS.surface,
    fontSize: 12,
    fontWeight: 'bold',
  },
  placeholderImage: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardContent: {
    padding: SPACING.md,
  },
  cardTitle: {
    ...TYPOGRAPHY.h3,
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
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  categoryBadge: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 4,
  },
  categoryBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.surface,
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
  emptySubtext: {
    ...TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
  },
});