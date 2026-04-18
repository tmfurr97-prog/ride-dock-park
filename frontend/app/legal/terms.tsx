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
    title: '1. Acceptance of Terms',
    body:
      'By creating an account or using DriveShare & Dock (the "Platform"), you agree to be bound by these Terms of Service, our Privacy Policy, and all applicable laws. If you do not agree, do not use the Platform.',
  },
  {
    title: '2. Platform Role (Broker Disclaimer)',
    body:
      'DriveShare & Dock is a technology platform that connects owners (Hosts) of RVs, land parcels, vehicle storage, and boats/docks with renters (Guests). We are NOT an insurer, broker, legal representative, fiduciary, or party to any rental agreement between users. All transactions are solely between Host and Guest.',
  },
  {
    title: '3. User Eligibility & Verification',
    body:
      'You must be at least 21 years old and legally permitted to rent or offer the relevant asset. All users pay a one-time $25 verification fee. You agree to provide truthful identification. We reserve the right to suspend, ban, or remove any account at our discretion.',
  },
  {
    title: '4. Listings, Insurance & Deposits',
    body:
      'Hosts represent that they hold title (or legal authority) to list the asset and carry valid insurance where required. Boat and RV listings MUST provide proof of insurance. Hosts set their own rental rate, add-on pricing, and refundable security deposit. Guests are solely responsible for damages in excess of the security deposit.',
  },
  {
    title: '5. Platform Fees & Commissions',
    body:
      'DriveShare & Dock retains a platform commission of 10% on rental subtotals for the first 6 months following Host signup, and 15% thereafter. A flat 10% fee applies to all add-ons. Fees are deducted from Host payouts. Fees are non-refundable except where required by law.',
  },
  {
    title: '6. Security Deposits',
    body:
      'Security deposits are collected as a pre-authorization hold on the Guest\'s payment method. Deposits are released 48 hours after the rental end date if no damage claim is opened by the Host. Disputed claims are mediated via our in-app messaging; unresolved claims may be escalated to civil court between the parties.',
  },
  {
    title: '7. Cancellations & Refunds',
    body:
      'Cancellation terms are set per-listing by the Host. Guests who cancel more than 72 hours before rental start receive a full rental refund less platform fees. Cancellations within 72 hours forfeit up to 50% of the rental at the Host\'s discretion. Security deposits are always refundable on cancelled rentals.',
  },
  {
    title: '8. Prohibited Conduct',
    body:
      'Users may not: (a) list stolen or misrepresented assets; (b) operate assets without required licenses; (c) harass or discriminate against other users; (d) conduct transactions off-platform to avoid fees; (e) upload fraudulent insurance documents. Violations result in immediate account termination and may be reported to authorities.',
  },
  {
    title: '9. Coast Guard & Safety Compliance',
    body:
      'Boat listings must provide life jackets in a quantity at least equal to the stated rental capacity. Guests are responsible for compliance with all USCG regulations, local boating laws, and operator licensing. Hosts may require proof of competency before releasing a vessel.',
  },
  {
    title: '10. Limitation of Liability',
    body:
      'TO THE MAXIMUM EXTENT PERMITTED BY LAW, DRIVESHARE & DOCK, ITS OFFICERS, EMPLOYEES, AND AFFILIATES SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, LOST PROFITS, OR LOST DATA ARISING FROM USE OF THE PLATFORM. OUR AGGREGATE LIABILITY SHALL NOT EXCEED THE FEES PAID BY YOU TO US IN THE PRECEDING 12 MONTHS.',
  },
  {
    title: '11. Indemnification',
    body:
      'You agree to indemnify and hold DriveShare & Dock harmless from claims, damages, losses, and legal fees arising out of your use of the Platform, your listings, your bookings, or your violation of these Terms or applicable law.',
  },
  {
    title: '12. Dispute Resolution & Arbitration',
    body:
      'Any dispute arising under these Terms shall first be attempted in good-faith negotiation. Unresolved disputes shall be submitted to binding arbitration under the rules of the American Arbitration Association, in the state of the Host\'s listed asset. You waive any right to a jury trial or class action.',
  },
  {
    title: '13. Governing Law',
    body:
      'These Terms are governed by the laws of the State of Delaware, USA, without regard to its conflict-of-law principles.',
  },
  {
    title: '14. Changes to Terms',
    body:
      'We may modify these Terms at any time. Continued use of the Platform after the effective date of revised Terms constitutes your acceptance.',
  },
  {
    title: '15. Contact',
    body:
      'Questions: legal@driveshareanddock.com. Effective date: June 2025.',
  },
];

export default function TermsOfService() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.surface} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Terms of Service</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.intro}>
          Welcome to DriveShare & Dock. Please read these Terms carefully. They
          govern your use of our marketplace for RV rentals, land stays, vehicle
          storage, and boat rentals & docks.
        </Text>

        {SECTIONS.map((s, idx) => (
          <View key={idx} style={styles.section}>
            <Text style={styles.sectionTitle}>{s.title}</Text>
            <Text style={styles.sectionBody}>{s.body}</Text>
          </View>
        ))}

        <View style={styles.disclaimerBox}>
          <Ionicons name="shield-checkmark" size={28} color={COLORS.primary} />
          <Text style={styles.disclaimerText}>
            DriveShare & Dock is a platform provider and does not provide
            insurance or legal representation.
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
