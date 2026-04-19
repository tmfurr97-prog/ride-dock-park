import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../../constants/theme';
import api from '../../services/api';
import LegalFooter from '../../components/LegalFooter';

export default function Favorites() {
  const router = useRouter();
  const [favorites, setFavorites] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      const res = await api.get('/api/favorites');
      setFavorites(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const removeFav = async (listingId: string) => {
    try {
      await api.delete(`/api/favorites/${listingId}`);
      setFavorites((f) => f.filter((x) => x.id !== listingId));
    } catch (e) {
      console.error(e);
    }
  };

  const renderCard = ({ item }: any) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => router.push(`/listing/${item.id}`)}
    >
      {item.images?.[0] ? (
        <Image source={{ uri: item.images[0] }} style={styles.image} />
      ) : (
        <View style={[styles.image, styles.imagePlaceholder]}>
          <Ionicons name="image" size={32} color={COLORS.textLight} />
        </View>
      )}
      <TouchableOpacity
        style={styles.heartBtn}
        onPress={() => removeFav(item.id)}
      >
        <Ionicons name="heart" size={20} color={COLORS.coral} />
      </TouchableOpacity>
      <View style={styles.cardBody}>
        <Text style={styles.cardTitle} numberOfLines={1}>{item.title}</Text>
        <Text style={styles.cardLocation} numberOfLines={1}>
          <Ionicons name="location-outline" size={12} /> {item.location}
        </Text>
        <Text style={styles.cardPrice}>
          ${item.price}{item.is_long_term ? '/mo' : '/day'}
        </Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Ionicons name="heart" size={24} color={COLORS.coral} />
        <Text style={styles.headerTitle}>Favorites</Text>
      </View>
      <FlatList
        data={favorites}
        renderItem={renderCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              load();
            }}
            tintColor={COLORS.primary}
          />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="heart-outline" size={64} color={COLORS.textLight} />
            <Text style={styles.emptyText}>
              {loading ? 'Loading…' : 'No favorites yet'}
            </Text>
            <Text style={styles.emptySubtext}>
              Tap the ❤️ icon on any listing to save it here.
            </Text>
          </View>
        }
      />
      <LegalFooter />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: { ...TYPOGRAPHY.h2, color: COLORS.text },
  list: { padding: SPACING.md, gap: SPACING.md },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    marginBottom: SPACING.md,
    overflow: 'hidden',
    ...SHADOWS.small,
  },
  image: { width: '100%', height: 180 },
  imagePlaceholder: {
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartBtn: {
    position: 'absolute',
    top: SPACING.sm,
    right: SPACING.sm,
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
    ...SHADOWS.small,
  },
  cardBody: { padding: SPACING.md },
  cardTitle: { ...TYPOGRAPHY.h3, color: COLORS.text, marginBottom: 2 },
  cardLocation: { fontSize: 13, color: COLORS.textLight, marginBottom: SPACING.xs },
  cardPrice: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.primary,
  },
  empty: {
    alignItems: 'center',
    padding: SPACING.xxl,
    gap: SPACING.sm,
  },
  emptyText: { ...TYPOGRAPHY.h3, marginTop: SPACING.md },
  emptySubtext: { fontSize: 13, color: COLORS.textLight, textAlign: 'center' },
});
