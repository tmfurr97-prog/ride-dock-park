import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { COLORS, SPACING, TYPOGRAPHY, SHADOWS } from '../constants/theme';
import { useAuthStore } from '../store/authStore';
import api from '../services/api';

const CATEGORIES = [
  { id: 'rv_rental', label: 'RV Rental', icon: 'car' },
  { id: 'land_stay', label: 'Land Stay', icon: 'home' },
  { id: 'vehicle_storage', label: 'Vehicle Storage', icon: 'cube' },
];

const RV_TYPES = ['Class A', 'Class B', 'Class C', 'Fifth Wheel', 'Travel Trailer', 'Toy Hauler'];
const HOOKUP_TYPES = ['Full Hookup', 'Water & Electric', 'Electric Only', 'Dry Camping'];
const SECURITY_FEATURES = ['Gated', 'Cameras', 'Lights', '24/7 Access', 'Security Guard'];

export default function CreateListing() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const [loading, setLoading] = useState(false);
  
  // Common fields
  const [selectedCategory, setSelectedCategory] = useState('rv_rental');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [location, setLocation] = useState('');
  const [images, setImages] = useState<string[]>([]);

  // RV Rental fields
  const [rvType, setRvType] = useState('');
  const [capacity, setCapacity] = useState('');
  const [power, setPower] = useState(false);
  const [water, setWater] = useState(false);
  const [sewage, setSewage] = useState(false);

  // Land Stay fields
  const [acreage, setAcreage] = useState('');
  const [hookupType, setHookupType] = useState('');
  const [utilities, setUtilities] = useState('');

  // Vehicle Storage fields
  const [length, setLength] = useState('');
  const [width, setWidth] = useState('');
  const [height, setHeight] = useState('');
  const [securityFeatures, setSecurityFeatures] = useState<string[]>([]);
  const [accessHours, setAccessHours] = useState('');

  const requestPermissions = async () => {
    const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
    const { status: galleryStatus } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (cameraStatus !== 'granted' || galleryStatus !== 'granted') {
      Alert.alert('Permission Required', 'Camera and gallery access are needed to add photos.');
      return false;
    }
    return true;
  };

  const pickImage = async (source: 'camera' | 'gallery') => {
    if (images.length >= 10) {
      Alert.alert('Limit Reached', 'You can upload up to 10 images.');
      return;
    }

    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    try {
      let result;
      if (source === 'camera') {
        result = await ImagePicker.launchCameraAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [4, 3],
          quality: 0.8,
          base64: true,
        });
      } else {
        result = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [4, 3],
          quality: 0.8,
          base64: true,
        });
      }

      if (!result.canceled && result.assets[0].base64) {
        const base64Image = `data:image/jpeg;base64,${result.assets[0].base64}`;
        setImages([...images, base64Image]);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const removeImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index));
  };

  const toggleSecurityFeature = (feature: string) => {
    if (securityFeatures.includes(feature)) {
      setSecurityFeatures(securityFeatures.filter(f => f !== feature));
    } else {
      setSecurityFeatures([...securityFeatures, feature]);
    }
  };

  const validateForm = () => {
    if (!title.trim() || !description.trim() || !price || !location.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return false;
    }

    if (parseFloat(price) <= 0) {
      Alert.alert('Error', 'Price must be greater than 0');
      return false;
    }

    if (images.length === 0) {
      Alert.alert('Error', 'Please add at least one image');
      return false;
    }

    // Category-specific validation
    if (selectedCategory === 'rv_rental') {
      if (!rvType || !capacity) {
        Alert.alert('Error', 'Please fill in RV type and capacity');
        return false;
      }
    } else if (selectedCategory === 'land_stay') {
      if (!acreage || !hookupType) {
        Alert.alert('Error', 'Please fill in acreage and hookup type');
        return false;
      }
    } else if (selectedCategory === 'vehicle_storage') {
      if (!length || !width || !height) {
        Alert.alert('Error', 'Please fill in storage dimensions');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      let amenities: any = {};

      if (selectedCategory === 'rv_rental') {
        amenities = {
          rv_type: rvType,
          capacity: parseInt(capacity),
          power,
          water,
          sewage,
        };
      } else if (selectedCategory === 'land_stay') {
        amenities = {
          acreage: parseFloat(acreage),
          hookup_type: hookupType,
          utilities,
        };
      } else if (selectedCategory === 'vehicle_storage') {
        amenities = {
          dimensions: {
            length: parseFloat(length),
            width: parseFloat(width),
            height: parseFloat(height),
          },
          security_features: securityFeatures,
          access_hours: accessHours,
        };
      }

      const response = await api.post('/api/listings', {
        category: selectedCategory,
        title: title.trim(),
        description: description.trim(),
        price: parseFloat(price),
        location: location.trim(),
        images,
        amenities,
      });

      Alert.alert('Success', 'Listing created successfully!', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to create listing'
      );
    } finally {
      setLoading(false);
    }
  };

  const renderCategorySelector = () => (
    <View style={styles.section}>
      <Text style={styles.label}>Category *</Text>
      <View style={styles.categoryGrid}>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat.id}
            style={[
              styles.categoryCard,
              selectedCategory === cat.id && styles.categoryCardActive,
            ]}
            onPress={() => setSelectedCategory(cat.id)}
          >
            <Ionicons
              name={cat.icon as any}
              size={32}
              color={selectedCategory === cat.id ? COLORS.surface : COLORS.primary}
            />
            <Text
              style={[
                styles.categoryLabel,
                selectedCategory === cat.id && styles.categoryLabelActive,
              ]}
            >
              {cat.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderImagePicker = () => (
    <View style={styles.section}>
      <Text style={styles.label}>Photos * ({images.length}/10)</Text>
      <View style={styles.imageGrid}>
        {images.map((img, index) => (
          <View key={index} style={styles.imageWrapper}>
            <Image source={{ uri: img }} style={styles.imageThumbnail} />
            <TouchableOpacity
              style={styles.removeImageButton}
              onPress={() => removeImage(index)}
            >
              <Ionicons name="close-circle" size={24} color={COLORS.error} />
            </TouchableOpacity>
          </View>
        ))}
        {images.length < 10 && (
          <>
            <TouchableOpacity
              style={styles.addImageButton}
              onPress={() => pickImage('camera')}
            >
              <Ionicons name="camera" size={32} color={COLORS.primary} />
              <Text style={styles.addImageText}>Camera</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.addImageButton}
              onPress={() => pickImage('gallery')}
            >
              <Ionicons name="images" size={32} color={COLORS.primary} />
              <Text style={styles.addImageText}>Gallery</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );

  const renderRVFields = () => (
    <>
      <View style={styles.section}>
        <Text style={styles.label}>RV Type *</Text>
        <View style={styles.chipContainer}>
          {RV_TYPES.map((type) => (
            <TouchableOpacity
              key={type}
              style={[
                styles.chip,
                rvType === type && styles.chipActive,
              ]}
              onPress={() => setRvType(type)}
            >
              <Text
                style={[
                  styles.chipText,
                  rvType === type && styles.chipTextActive,
                ]}
              >
                {type}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Capacity (people) *</Text>
        <TextInput
          style={styles.input}
          value={capacity}
          onChangeText={setCapacity}
          placeholder="e.g., 4"
          placeholderTextColor={COLORS.textLight}
          keyboardType="number-pad"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Amenities</Text>
        <View style={styles.checkboxContainer}>
          <TouchableOpacity
            style={styles.checkbox}
            onPress={() => setPower(!power)}
          >
            <Ionicons
              name={power ? 'checkbox' : 'square-outline'}
              size={24}
              color={COLORS.primary}
            />
            <Text style={styles.checkboxLabel}>Power</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.checkbox}
            onPress={() => setWater(!water)}
          >
            <Ionicons
              name={water ? 'checkbox' : 'square-outline'}
              size={24}
              color={COLORS.primary}
            />
            <Text style={styles.checkboxLabel}>Water</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.checkbox}
            onPress={() => setSewage(!sewage)}
          >
            <Ionicons
              name={sewage ? 'checkbox' : 'square-outline'}
              size={24}
              color={COLORS.primary}
            />
            <Text style={styles.checkboxLabel}>Sewage</Text>
          </TouchableOpacity>
        </View>
      </View>
    </>
  );

  const renderLandFields = () => (
    <>
      <View style={styles.section}>
        <Text style={styles.label}>Acreage *</Text>
        <TextInput
          style={styles.input}
          value={acreage}
          onChangeText={setAcreage}
          placeholder="e.g., 2.5"
          placeholderTextColor={COLORS.textLight}
          keyboardType="decimal-pad"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Hookup Type *</Text>
        <View style={styles.chipContainer}>
          {HOOKUP_TYPES.map((type) => (
            <TouchableOpacity
              key={type}
              style={[
                styles.chip,
                hookupType === type && styles.chipActive,
              ]}
              onPress={() => setHookupType(type)}
            >
              <Text
                style={[
                  styles.chipText,
                  hookupType === type && styles.chipTextActive,
                ]}
              >
                {type}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Utilities Available</Text>
        <TextInput
          style={styles.input}
          value={utilities}
          onChangeText={setUtilities}
          placeholder="e.g., Water, Electric, Sewer"
          placeholderTextColor={COLORS.textLight}
        />
      </View>
    </>
  );

  const renderStorageFields = () => (
    <>
      <View style={styles.section}>
        <Text style={styles.label}>Dimensions (feet) *</Text>
        <View style={styles.dimensionRow}>
          <View style={styles.dimensionInput}>
            <Text style={styles.dimensionLabel}>Length</Text>
            <TextInput
              style={styles.input}
              value={length}
              onChangeText={setLength}
              placeholder="20"
              placeholderTextColor={COLORS.textLight}
              keyboardType="decimal-pad"
            />
          </View>
          <View style={styles.dimensionInput}>
            <Text style={styles.dimensionLabel}>Width</Text>
            <TextInput
              style={styles.input}
              value={width}
              onChangeText={setWidth}
              placeholder="10"
              placeholderTextColor={COLORS.textLight}
              keyboardType="decimal-pad"
            />
          </View>
          <View style={styles.dimensionInput}>
            <Text style={styles.dimensionLabel}>Height</Text>
            <TextInput
              style={styles.input}
              value={height}
              onChangeText={setHeight}
              placeholder="8"
              placeholderTextColor={COLORS.textLight}
              keyboardType="decimal-pad"
            />
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Security Features</Text>
        <View style={styles.chipContainer}>
          {SECURITY_FEATURES.map((feature) => (
            <TouchableOpacity
              key={feature}
              style={[
                styles.chip,
                securityFeatures.includes(feature) && styles.chipActive,
              ]}
              onPress={() => toggleSecurityFeature(feature)}
            >
              <Text
                style={[
                  styles.chipText,
                  securityFeatures.includes(feature) && styles.chipTextActive,
                ]}
              >
                {feature}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Access Hours</Text>
        <TextInput
          style={styles.input}
          value={accessHours}
          onChangeText={setAccessHours}
          placeholder="e.g., 6 AM - 10 PM or 24/7"
          placeholderTextColor={COLORS.textLight}
        />
      </View>
    </>
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
        <Text style={styles.headerTitle}>Create Listing</Text>
        <View style={styles.headerSpacer} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {renderCategorySelector()}

          <View style={styles.section}>
            <Text style={styles.label}>Title *</Text>
            <TextInput
              style={styles.input}
              value={title}
              onChangeText={setTitle}
              placeholder="e.g., Spacious RV with Full Hookup"
              placeholderTextColor={COLORS.textLight}
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>Description *</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={description}
              onChangeText={setDescription}
              placeholder="Describe your listing, features, and what makes it special..."
              placeholderTextColor={COLORS.textLight}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>
              Price * (per {selectedCategory === 'rv_rental' ? 'day' : selectedCategory === 'land_stay' ? 'night' : 'month'})
            </Text>
            <View style={styles.priceInput}>
              <Text style={styles.priceSymbol}>$</Text>
              <TextInput
                style={[styles.input, styles.priceField]}
                value={price}
                onChangeText={setPrice}
                placeholder="0.00"
                placeholderTextColor={COLORS.textLight}
                keyboardType="decimal-pad"
              />
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.label}>Location *</Text>
            <TextInput
              style={styles.input}
              value={location}
              onChangeText={setLocation}
              placeholder="e.g., Yosemite National Park, CA"
              placeholderTextColor={COLORS.textLight}
            />
          </View>

          {selectedCategory === 'rv_rental' && renderRVFields()}
          {selectedCategory === 'land_stay' && renderLandFields()}
          {selectedCategory === 'vehicle_storage' && renderStorageFields()}

          {renderImagePicker()}

          <TouchableOpacity
            style={[styles.submitButton, loading && styles.buttonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={COLORS.surface} />
            ) : (
              <Text style={styles.submitButtonText}>Create Listing</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
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
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    padding: SPACING.lg,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  label: {
    ...TYPOGRAPHY.body,
    fontWeight: '600',
    marginBottom: SPACING.sm,
    color: COLORS.text,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: SPACING.md,
    fontSize: 16,
    backgroundColor: COLORS.surface,
    color: COLORS.text,
  },
  textArea: {
    minHeight: 100,
  },
  priceInput: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    paddingLeft: SPACING.md,
  },
  priceSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginRight: SPACING.xs,
  },
  priceField: {
    flex: 1,
    borderWidth: 0,
  },
  categoryGrid: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  categoryCard: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.md,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.border,
    ...SHADOWS.small,
  },
  categoryCardActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  categoryLabel: {
    ...TYPOGRAPHY.caption,
    fontWeight: '600',
    marginTop: SPACING.xs,
    textAlign: 'center',
    color: COLORS.text,
  },
  categoryLabelActive: {
    color: COLORS.surface,
  },
  imageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  imageWrapper: {
    position: 'relative',
  },
  imageThumbnail: {
    width: 100,
    height: 100,
    borderRadius: 8,
    backgroundColor: COLORS.background,
  },
  removeImageButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
  },
  addImageButton: {
    width: 100,
    height: 100,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
  },
  addImageText: {
    ...TYPOGRAPHY.caption,
    marginTop: SPACING.xs,
    color: COLORS.primary,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  chip: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.primary,
    backgroundColor: COLORS.surface,
  },
  chipActive: {
    backgroundColor: COLORS.primary,
  },
  chipText: {
    fontSize: 14,
    color: COLORS.primary,
  },
  chipTextActive: {
    color: COLORS.surface,
    fontWeight: '600',
  },
  checkboxContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.md,
  },
  checkbox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    paddingRight: SPACING.md,
  },
  checkboxLabel: {
    ...TYPOGRAPHY.body,
  },
  dimensionRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  dimensionInput: {
    flex: 1,
  },
  dimensionLabel: {
    ...TYPOGRAPHY.caption,
    marginBottom: SPACING.xs,
    textAlign: 'center',
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.lg,
    marginBottom: SPACING.xl,
    minHeight: 48,
    ...SHADOWS.medium,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    ...TYPOGRAPHY.button,
    fontSize: 18,
  },
});