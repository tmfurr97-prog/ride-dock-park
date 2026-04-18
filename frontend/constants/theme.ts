export const COLORS = {
  // Forest Green Palette
  primary: '#1B4332',      // Deep Forest
  secondary: '#2D6A4F',    // Mid Forest
  accent: '#40916C',       // Light Forest
  coral: '#E76F51',        // Coral Orange - CTA accent
  coralDark: '#D65A3C',    // Coral Orange pressed state
  background: '#F8F9FA',   // Off-white
  surface: '#FFFFFF',      // White
  text: '#212529',         // Dark Gray
  textLight: '#6C757D',    // Medium Gray
  error: '#D62828',        // Deep Red
  success: '#40916C',      // Light Forest
  border: '#DEE2E6',       // Light Gray
  disabled: '#ADB5BD',     // Gray
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const TYPOGRAPHY = {
  h1: {
    fontSize: 32,
    fontWeight: 'bold' as const,
    color: COLORS.text,
  },
  h2: {
    fontSize: 24,
    fontWeight: 'bold' as const,
    color: COLORS.text,
  },
  h3: {
    fontSize: 20,
    fontWeight: '600' as const,
    color: COLORS.text,
  },
  body: {
    fontSize: 16,
    fontWeight: 'normal' as const,
    color: COLORS.text,
  },
  caption: {
    fontSize: 14,
    fontWeight: 'normal' as const,
    color: COLORS.textLight,
  },
  button: {
    fontSize: 16,
    fontWeight: '600' as const,
    color: COLORS.surface,
  },
};

export const SHADOWS = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  large: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 8,
  },
};