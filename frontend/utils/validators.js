/**
 * Validation utilities for exchange items
 */

/**
 * @typedef {Object} ValidationResult
 * @property {boolean} valid
 * @property {string} [error]
 */

// Validation constants
const MIN_ITEM_NAME_LENGTH = 3;
const MAX_ITEM_NAME_LENGTH = 100;
const MAX_DESCRIPTION_LENGTH = 500;
const MIN_VALUE = 1;
const MAX_VALUE = 10000000;
const MIN_DURATION = 1;
const MAX_DURATION = 365;

// Expanded categories matching frontend definitions
const VALID_CATEGORIES = new Set([
  // Permanent exchange categories
  'cars',
  'real_estate',
  'electronics',
  'entertainment_tech',
  'everyday_clothes',
  'accessories',
  'kitchen_furniture',
  'collectibles',
  'animals_plants',
  'money_crypto',
  'securities',

  // Temporary exchange categories
  'bicycle',
  'electric_transport',
  'sports_transport',
  'hand_tools',
  'power_tools',
  'industrial_equipment',
  'photo_video',
  'audio_equipment',
  'sports_gear',
  'tourism_camping',
  'games_vr',
  'music_instruments',
  'costumes',
  'event_accessories',
  'subscriptions',
  'temporary_loan',
  'consulting',

  // Legacy categories (for backward compatibility)
  'furniture',
  'transport',
  'money',
  'services',
  'other'
]);

/**
 * Validate permanent exchange item
 */
export function validatePermanentItem(item) {
  if (!item.category || !VALID_CATEGORIES.has(item.category)) {
    return { valid: false, error: 'Invalid or missing category' };
  }

  if (!item.item_name || item.item_name.length < MIN_ITEM_NAME_LENGTH) {
    return { valid: false, error: `Item name must be at least ${MIN_ITEM_NAME_LENGTH} characters` };
  }

  if (item.item_name.length > MAX_ITEM_NAME_LENGTH) {
    return { valid: false, error: `Item name cannot exceed ${MAX_ITEM_NAME_LENGTH} characters` };
  }

  const value = parseFloat(item.value_tenge);
  if (isNaN(value) || value < MIN_VALUE) {
    return { valid: false, error: `Value must be at least ${MIN_VALUE} ₸` };
  }

  if (value > MAX_VALUE) {
    return { valid: false, error: `Value cannot exceed ${MAX_VALUE} ₸` };
  }

  if (item.description && item.description.length > MAX_DESCRIPTION_LENGTH) {
    return { valid: false, error: `Description cannot exceed ${MAX_DESCRIPTION_LENGTH} characters` };
  }

  return { valid: true };
}

/**
 * Validate temporary exchange item
 */
export function validateTemporaryItem(item) {
  if (!item.category || !VALID_CATEGORIES.has(item.category)) {
    return { valid: false, error: 'Invalid or missing category' };
  }

  if (!item.item_name || item.item_name.length < MIN_ITEM_NAME_LENGTH) {
    return { valid: false, error: `Item name must be at least ${MIN_ITEM_NAME_LENGTH} characters` };
  }

  if (item.item_name.length > MAX_ITEM_NAME_LENGTH) {
    return { valid: false, error: `Item name cannot exceed ${MAX_ITEM_NAME_LENGTH} characters` };
  }

  const value = parseFloat(item.value_tenge);
  if (isNaN(value) || value < MIN_VALUE) {
    return { valid: false, error: `Value must be at least ${MIN_VALUE} ₸` };
  }

  if (value > MAX_VALUE) {
    return { valid: false, error: `Value cannot exceed ${MAX_VALUE} ₸` };
  }

  const duration = parseInt(item.duration_days);
  if (isNaN(duration) || duration < MIN_DURATION) {
    return { valid: false, error: `Duration must be at least ${MIN_DURATION} day` };
  }

  if (duration > MAX_DURATION) {
    return { valid: false, error: `Duration cannot exceed ${MAX_DURATION} days` };
  }

  if (item.description && item.description.length > MAX_DESCRIPTION_LENGTH) {
    return { valid: false, error: `Description cannot exceed ${MAX_DESCRIPTION_LENGTH} characters` };
  }

  return { valid: true };
}

/**
 * Calculate daily rate for temporary items
 */
export function calculateDailyRate(value, durationDays) {
  if (!durationDays || durationDays <= 0) return 0;
  return value / durationDays;
}

/**
 * Get quality label based on score
 */
export function getQualityLabel(score) {
  if (score >= 0.85) return 'excellent';
  if (score >= 0.70) return 'good';
  if (score >= 0.50) return 'fair';
  return 'poor';
}

/**
 * Get color based on score
 */
export function getScoreColor(score) {
  if (score >= 0.85) return 'bg-green-100 border-green-400 text-green-900';
  if (score >= 0.70) return 'bg-yellow-100 border-yellow-400 text-yellow-900';
  return 'bg-red-100 border-red-400 text-red-900';
}

/**
 * Format score as percentage
 */
export function formatScore(score) {
  return `${(score * 100).toFixed(0)}%`;
}

