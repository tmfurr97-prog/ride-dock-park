import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Dimensions,
  TextInput,
  Modal,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../../constants/theme';
import { useAuthStore } from '../../store/authStore';
import api from '../../services/api';

const { width } = Dimensions.get('window');

export default function ListingDetail() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const user = useAuthStore((state) => state.user);
  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [bookingTosAccepted, setBookingTosAccepted] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);

  useEffect(() => {
    loadListing();
  }, [id]);

  const loadListing = async () => {
    try {
      const response = await api.get(`/api/listings/${id}`);
      setListing(response.data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load listing');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const handleContact = () => {
    if (!user?.is_verified) {
      Alert.alert(
        'Verification Required',
        'You must be verified to contact hosts.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Verify Now', onPress: () => router.push('/verification') },
        ]
      );
      return;
    }

    // Navigate to chat
    const userId = user.id;
    const otherUserId = listing.owner_id;
    const conversationId = [userId, otherUserId].sort().join('_');
    router.push(`/chat/${conversationId}`);
  };

  const handleBook = async () => {
    if (!user?.is_verified) {
      Alert.alert(
        'Verification Required',
        'You must be verified to book listings.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Verify Now', onPress: () => router.push('/verification') },
        ]
      );
      return;
    }

    if (!startDate || !endDate) {
      Alert.alert('Error', 'Please select start and end dates');
      return;
    }

    if (!bookingTosAccepted) {
      Alert.alert(
        'Terms of Service',
        'You must agree to the Terms of Service to complete a booking.'
      );
      return;
    }

    setBookingLoading(true);
    try {
      const response = await api.post('/api/bookings', {
        listing_id: listing.id,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        tos_accepted: true,
      });

      const statusMsg =
        response.data.status === 'awaiting_insurance_review'
          ? "\n\nYour booking is pending the host's insurance approval."
          : response.data.status === 'awaiting_host_approval'
          ? "\n\nYour booking is pending host approval."
          : '';

      // Initiate payment immediately — charge held until host approves
      try {
        const originUrl = (process.env.EXPO_PUBLIC_BACKEND_URL || '').replace('/api', '');
        const payRes = await api.post(
          `/api/payments/booking/create-checkout?booking_id=${response.data.id}&origin_url=${encodeURIComponent(originUrl)}`
        );
        if (payRes.data?.url) {
          setShowBookingModal(false);
          // Open Stripe Checkout
          if (typeof window !== 'undefined') {
            window.location.href = payRes.data.url;
          } else {
            Alert.alert('Open Payment', `Go to: ${payRes.data.url}`);
          }
          return;
        }
      } catch (payErr: any) {
        console.log('Payment session error:', payErr);
      }

      Alert.alert(
        'Booking Requested!',
        `Total: $${response.data.total_price.toFixed(2)}` +
          (response.data.security_deposit
            ? `\n(includes $${response.data.security_deposit} refundable deposit hold)`
            : '') +
          statusMsg,
        [
          {
            text: 'View Bookings',
            onPress: () => {
              setShowBookingModal(false);
              router.push('/(tabs)/bookings');
            },
          },
        ]
      );
    } catch (error: any) {
      Alert.alert(
        'Booking Failed',
        error.response?.data?.detail || 'Could not create booking'
      );
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  if (!listing) return null;

  const priceUnit = listing.category === 'rv_rental' ? 'day' : listing.category === 'land_stay' ? 'night' : 'month';

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.surface} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Listing Details</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={async () => {
            try {
              if (isFavorite) {
                await api.delete(`/api/favorites/${listing.id}`);
                setIsFavorite(false);
              } else {
                await api.post(`/api/favorites/${listing.id}`);
                setIsFavorite(true);
              }
            } catch (e) {
              Alert.alert('Error', 'Please log in to save favorites');
            }
          }}
        >
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={24}
            color={isFavorite ? COLORS.coral : COLORS.surface}
          />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Image Gallery */}
        {listing.images && listing.images.length > 0 && (
          <View style={styles.imageContainer}>
            <ScrollView
              horizontal
              pagingEnabled
              showsHorizontalScrollIndicator={false}
              onScroll={(e) => {
                const x = e.nativeEvent.contentOffset.x;
                const index = Math.round(x / width);
                setCurrentImageIndex(index);
              }}
              scrollEventThrottle={16}
            >
              {listing.images.map((img: string, idx: number) => (
                <Image
                  key={idx}
                  source={{ uri: img }}
                  style={styles.image}
                  resizeMode="cover"
                />
              ))}
            </ScrollView>
            <View style={styles.imageIndicator}>
              <Text style={styles.imageIndicatorText}>
                {currentImageIndex + 1} / {listing.images.length}
              </Text>
            </View>
          </View>
        )}

        <View style={styles.content}>
          {/* Title & Price */}
          <View style={styles.titleSection}>
            <Text style={styles.title}>{listing.title}</Text>
            <Text style={styles.price}>${listing.price}/{priceUnit}</Text>
          </View>

          {/* Location */}
          <View style={styles.locationRow}>
            <Ionicons name="location" size={20} color={COLORS.primary} />
            <Text style={styles.location}>{listing.location}</Text>
          </View>

          {/* Owner Info */}
          <View style={styles.ownerCard}>
            <View style={styles.ownerAvatar}>
              <Ionicons name="person" size={24} color={COLORS.surface} />
            </View>
            <View style={styles.ownerInfo}>
              <Text style={styles.ownerName}>Hosted by {listing.owner_name}</Text>
              <Text style={styles.ownerLabel}>Property Owner</Text>
            </View>
          </View>

          {/* Description */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Description</Text>
            <Text style={styles.description}>{listing.description}</Text>
          </View>

          {/* House Rules */}
          {listing.house_rules ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>House Rules</Text>
              <View style={styles.houseRulesBox}>
                <Ionicons name="document-text" size={20} color={COLORS.primary} />
                <Text style={styles.houseRulesText}>{listing.house_rules}</Text>
              </View>
            </View>
          ) : null}

          {/* Hourly / Max RV Length Badges */}
          {(listing.accepts_hourly || listing.max_rv_length > 0) && (
            <View style={styles.badgeRow}>
              {listing.accepts_hourly ? (
                <View style={styles.featBadge}>
                  <Ionicons name="time" size={14} color={COLORS.primary} />
                  <Text style={styles.featBadgeText}>
                    Hourly: ${listing.hourly_rate}/hr
                  </Text>
                </View>
              ) : null}
              {listing.max_rv_length > 0 ? (
                <View style={styles.featBadge}>
                  <Ionicons name="resize" size={14} color={COLORS.primary} />
                  <Text style={styles.featBadgeText}>
                    Max {listing.max_rv_length} ft
                  </Text>
                </View>
              ) : null}
            </View>
          )}

          {/* Category-specific Amenities */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Details</Text>
            
            {listing.category === 'rv_rental' && (
              <>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>RV Type:</Text>
                  <Text style={styles.detailValue}>{listing.amenities.rv_type}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Capacity:</Text>
                  <Text style={styles.detailValue}>{listing.amenities.capacity} people</Text>
                </View>
                <View style={styles.amenitiesRow}>
                  {listing.amenities.power && (
                    <View style={styles.amenityChip}>
                      <Ionicons name="flash" size={16} color={COLORS.primary} />
                      <Text style={styles.amenityText}>Power</Text>
                    </View>
                  )}
                  {listing.amenities.water && (
                    <View style={styles.amenityChip}>
                      <Ionicons name="water" size={16} color={COLORS.primary} />
                      <Text style={styles.amenityText}>Water</Text>
                    </View>
                  )}
                  {listing.amenities.sewage && (
                    <View style={styles.amenityChip}>
                      <Ionicons name="trash" size={16} color={COLORS.primary} />
                      <Text style={styles.amenityText}>Sewage</Text>
                    </View>
                  )}
                </View>
              </>
            )}

            {listing.category === 'land_stay' && (
              <>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Acreage:</Text>
                  <Text style={styles.detailValue}>{listing.amenities.acreage} acres</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Hookup Type:</Text>
                  <Text style={styles.detailValue}>{listing.amenities.hookup_type}</Text>
                </View>
                {listing.amenities.utilities && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Utilities:</Text>
                    <Text style={styles.detailValue}>{listing.amenities.utilities}</Text>
                  </View>
                )}
              </>
            )}

            {listing.category === 'vehicle_storage' && (
              <>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Dimensions:</Text>
                  <Text style={styles.detailValue}>
                    {listing.amenities.dimensions.length}' × {listing.amenities.dimensions.width}' × {listing.amenities.dimensions.height}'
                  </Text>
                </View>
                {listing.amenities.access_hours && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Access Hours:</Text>
                    <Text style={styles.detailValue}>{listing.amenities.access_hours}</Text>
                  </View>
                )}
                {listing.amenities.security_features && listing.amenities.security_features.length > 0 && (
                  <View style={styles.amenitiesRow}>
                    {listing.amenities.security_features.map((feature: string, idx: number) => (
                      <View key={idx} style={styles.amenityChip}>
                        <Ionicons name="shield-checkmark" size={16} color={COLORS.primary} />
                        <Text style={styles.amenityText}>{feature}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </>
            )}
          </View>
        </View>
      </ScrollView>

      {/* Action Buttons */}
      {listing.owner_id !== user?.id && (
        <View style={styles.actionBar}>
          <TouchableOpacity
            style={styles.contactButton}
            onPress={handleContact}
          >
            <Ionicons name="chatbubble" size={20} color={COLORS.primary} />
            <Text style={styles.contactButtonText}>Contact</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.bookButton}
            onPress={() => setShowBookingModal(true)}
          >
            <Text style={styles.bookButtonText}>Book Now</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Booking Modal */}
      <Modal
        visible={showBookingModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowBookingModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Book This Listing</Text>
              <TouchableOpacity onPress={() => setShowBookingModal(false)}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <Text style={styles.inputLabel}>Start Date (YYYY-MM-DD)</Text>
              <TextInput
                style={styles.input}
                value={startDate}
                onChangeText={setStartDate}
                placeholder="2025-07-01"
                placeholderTextColor={COLORS.textLight}
              />

              <Text style={styles.inputLabel}>End Date (YYYY-MM-DD)</Text>
              <TextInput
                style={styles.input}
                value={endDate}
                onChangeText={setEndDate}
                placeholder="2025-07-05"
                placeholderTextColor={COLORS.textLight}
              />

              <View style={styles.depositNotice}>
                <Ionicons name="information-circle" size={20} color={COLORS.primary} />
                <Text style={styles.depositNoticeText}>
                  Security deposits are held as a pre-authorization and released
                  48 hours after the rental ends if no damages are reported.
                </Text>
              </View>

              <TouchableOpacity
                style={styles.tosRow}
                onPress={() => setBookingTosAccepted(!bookingTosAccepted)}
                activeOpacity={0.7}
              >
                <Ionicons
                  name={bookingTosAccepted ? 'checkbox' : 'square-outline'}
                  size={24}
                  color={COLORS.primary}
                />
                <Text style={styles.tosText}>
                  I agree to the{' '}
                  <Text
                    style={styles.tosLink}
                    onPress={(e) => {
                      e.stopPropagation?.();
                      setShowBookingModal(false);
                      router.push('/legal/terms');
                    }}
                  >
                    Terms of Service
                  </Text>
                  , and accept that FurrstCamp Travel is a platform provider and
                  does not provide insurance or legal representation.
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.submitButton, bookingLoading && styles.buttonDisabled]}
                onPress={handleBook}
                disabled={bookingLoading}
              >
                {bookingLoading ? (
                  <ActivityIndicator color={COLORS.surface} />
                ) : (
                  <Text style={styles.submitButtonText}>Confirm Booking</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  headerSpacer: {
    width: 40,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  imageContainer: {
    position: 'relative',
  },
  image: {
    width: width,
    height: 300,
    backgroundColor: COLORS.background,
  },
  imageIndicator: {
    position: 'absolute',
    bottom: SPACING.md,
    right: SPACING.md,
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: 16,
  },
  imageIndicatorText: {
    color: COLORS.surface,
    fontSize: 14,
    fontWeight: '600',
  },
  content: {
    padding: SPACING.lg,
  },
  titleSection: {
    marginBottom: SPACING.md,
  },
  title: {
    ...TYPOGRAPHY.h1,
    fontSize: 28,
    marginBottom: SPACING.sm,
  },
  price: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  location: {
    ...TYPOGRAPHY.body,
    color: COLORS.textLight,
  },
  ownerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  ownerAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  ownerInfo: {
    flex: 1,
  },
  ownerName: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
  },
  ownerLabel: {
    ...TYPOGRAPHY.caption,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h3,
    marginBottom: SPACING.md,
  },
  description: {
    ...TYPOGRAPHY.body,
    lineHeight: 24,
    color: COLORS.text,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  detailLabel: {
    ...TYPOGRAPHY.body,
    color: COLORS.textLight,
  },
  detailValue: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
  },
  amenitiesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  amenityChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    backgroundColor: COLORS.background,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  amenityText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
  },
  actionBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.md,
    ...SHADOWS.large,
  },
  contactButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    padding: SPACING.md,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: COLORS.primary,
    backgroundColor: COLORS.surface,
  },
  contactButtonText: {
    ...TYPOGRAPHY.button,
    color: COLORS.primary,
  },
  bookButton: {
    flex: 2,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: SPACING.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bookButtonText: {
    ...TYPOGRAPHY.button,
    fontSize: 18,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingBottom: SPACING.xxl,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalTitle: {
    ...TYPOGRAPHY.h2,
  },
  modalBody: {
    padding: SPACING.lg,
  },
  inputLabel: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    marginBottom: SPACING.sm,
    marginTop: SPACING.md,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: SPACING.md,
    fontSize: 16,
    backgroundColor: COLORS.background,
    color: COLORS.text,
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.lg,
    minHeight: 48,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    ...TYPOGRAPHY.button,
    fontSize: 18,
  },
  depositNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    backgroundColor: '#F0F7F0',
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: 6,
    marginTop: SPACING.lg,
  },
  depositNoticeText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.text,
  },
  tosRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginTop: SPACING.md,
    padding: SPACING.md,
    backgroundColor: COLORS.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  tosText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.text,
  },
  tosLink: {
    color: COLORS.primary,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  houseRulesBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    backgroundColor: '#F0F7F0',
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: 6,
  },
  houseRulesText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.text,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
    paddingHorizontal: SPACING.md,
    flexWrap: 'wrap',
  },
  featBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    backgroundColor: '#F0F7F0',
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  featBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
});