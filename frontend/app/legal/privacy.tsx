import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, TYPOGRAPHY } from '../../constants/theme';

const SECTIONS = [
  {
    title: '1. Introduction',
    body:
      'FurrstCamp Travel ("we", "our", "us") respects your privacy. This Privacy Policy explains what data we collect, how we use it, and your rights. By using our Platform, you consent to the practices described here.',
  },
  {
    title: '2. Information We Collect',
    body:
      'Account Data: name, email, phone number, password (hashed), identity verification status.\n\nListing Data: photos, descriptions, location, pricing, insurance documentation you upload.\n\nTransaction Data: bookings, payment amounts, security deposit holds, add-on selections, fees. Payment card details are processed by Stripe and never stored on our servers.\n\nDevice & Usage Data: IP address, device type, OS, app version, crash logs, approximate location (if granted), and interaction analytics.\n\nCommunications: messages sent between users via the in-app chat.',
  },
  {
    title: '3. How We Use Your Information',
    body:
      '• Create and manage your account and identity verification.\n• Enable bookings, payments, payouts, and dispute resolution between users.\n• Calculate platform commission (10% intro / 15% standard + 10% flat on add-ons).\n• Send booking confirmations, security-deposit notices, and service messages.\n• Prevent fraud, enforce our Terms, and comply with legal obligations.\n• Improve product performance and troubleshoot issues.',
  },
  {
    title: '4. Legal Bases (for EU/UK Users)',
    body:
      'We process your data under: (a) contract — to deliver the service you signed up for; (b) legitimate interest — fraud prevention, product improvement; (c) consent — where required (e.g., marketing); (d) legal obligation — tax records, law enforcement requests.',
  },
  {
    title: '5. Sharing Your Information',
    body:
      'We share data only as needed to operate the marketplace:\n\n• With other users — your name, profile photo, listing/booking info, and messages are visible to the counterparty.\n• Stripe — for payment processing and payouts (see Stripe Privacy Policy).\n• Hosting & infrastructure providers — Railway, MongoDB Atlas, Expo, AWS (for storage, compute, and analytics).\n• Law enforcement — when legally required or to protect users.\n\nWe do NOT sell your personal data to third parties.',
  },
  {
    title: '6. Insurance & Verification Documents',
    body:
      'Proof of insurance, security-deposit holds, and verification documents uploaded to the Platform are stored securely and shared only with the booking counterparty and, when required, law enforcement or our payment processor.',
  },
  {
    title: '7. Cookies & Tracking',
    body:
      'Our mobile app uses limited analytics to measure performance and crashes. We do not use advertising cookies. The web admin panel may use essential session cookies required for login.',
  },
  {
    title: '8. Data Retention',
    body:
      'Account data: retained while your account is active plus 7 years for tax and legal records.\n\nTransaction/booking data: 7 years (tax, dispute, and anti-fraud compliance).\n\nSecurity deposit records: until fully released + 2 years.\n\nMessages: up to 2 years after the related booking ends.\n\nVerification documents: up to 2 years after account closure.',
  },
  {
    title: '9. Your Rights',
    body:
      'You may:\n• Access, correct, or delete your account data.\n• Export your data in a portable format.\n• Opt out of non-essential communications.\n• Object to or restrict certain processing (EU/UK/CA residents).\n• Lodge a complaint with a supervisory authority.\n\nTo exercise these rights, email privacy@furrstcamp.com. We respond within 30 days.',
  },
  {
    title: '10. California Privacy (CCPA/CPRA)',
    body:
      'California residents have additional rights: to know what personal information is collected, to delete it, to correct it, and to opt out of sale/share. We do not sell personal information. Requests: privacy@furrstcamp.com.',
  },
  {
    title: '11. Children',
    body:
      'Our Platform is not intended for users under 18. We do not knowingly collect information from minors. If you believe a minor has registered, contact us immediately and we will delete the account.',
  },
  {
    title: '12. Security',
    body:
      'We use industry-standard measures: bcrypt password hashing, TLS/HTTPS encryption in transit, encrypted storage at rest, JWT-based authentication, and Stripe PCI-compliant payment handling. No method is 100% secure; please use a strong unique password and keep your login credentials private.',
  },
  {
    title: '13. International Transfers',
    body:
      'Your data may be stored and processed in the United States and other countries where our infrastructure providers operate. We use standard contractual clauses and commercially reasonable safeguards for cross-border transfers.',
  },
  {
    title: '14. Changes to This Policy',
    body:
      'We may update this Privacy Policy from time to time. Material changes will be announced in-app at least 30 days before taking effect. Continued use after the effective date constitutes acceptance.',
  },
  {
    title: '15. Contact Us',
    body:
      'Privacy inquiries: privacy@furrstcamp.com\nData Protection Officer: dpo@furrstcamp.com\n\nEffective date: June 2025.',
  },
];

export default function PrivacyPolicy() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.surface} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Privacy Policy</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.intro}>
          Your privacy matters. This policy explains how FurrstCamp Travel
          collects, uses, and protects your information.
        </Text>

        {SECTIONS.map((s, idx) => (
          <View key={idx} style={styles.section}>
            <Text style={styles.sectionTitle}>{s.title}</Text>
            <Text style={styles.sectionBody}>{s.body}</Text>
          </View>
        ))}

        <View style={styles.disclaimerBox}>
          <Ionicons name="lock-closed" size={28} color={COLORS.primary} />
          <Text style={styles.disclaimerText}>
            We never sell your personal data. Payment details are processed
            securely by Stripe and never stored on our servers.
          </Text>
        </View>
      </ScrollView>
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
  content: {
    padding: SPACING.lg,
  },
  intro: {
    ...TYPOGRAPHY.body,
    marginBottom: SPACING.lg,
    fontStyle: 'italic',
    color: COLORS.textLight,
    lineHeight: 22,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    ...TYPOGRAPHY.h3,
    color: COLORS.primary,
    marginBottom: SPACING.sm,
  },
  sectionBody: {
    ...TYPOGRAPHY.body,
    lineHeight: 22,
    color: COLORS.text,
  },
  disclaimerBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: SPACING.lg,
    borderWidth: 2,
    borderColor: COLORS.primary,
    marginTop: SPACING.lg,
    marginBottom: SPACING.xxl,
  },
  disclaimerText: {
    ...TYPOGRAPHY.body,
    flex: 1,
    fontWeight: '600',
    color: COLORS.text,
  },
});
