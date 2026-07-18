/**
 * Centralized Icon Registry — Mobile App
 *
 * All Expo Vector Icons used across the ZOZI mobile app are exported from here.
 * Import icons from this file instead of directly from "@expo/vector-icons".
 *
 * Usage:
 *   import { Ionicons, Feather, IONICON, FEATHER } from "@/lib/icons";
 *
 *   // Use typed string constants (recommended):
 *   <Ionicons name={IONICON.CART}   size={24} color={theme.colors.brand} />
 *   <Feather  name={FEATHER.TRASH}  size={18} color="#ef4444" />
 *
 *   // Or use the raw string (still type-safe via React.ComponentProps):
 *   <Ionicons name="cart" size={24} color={theme.colors.brand} />
 */

import { Ionicons as _Ionicons, Feather as _Feather } from "@expo/vector-icons";
import type React from "react";

// Re-export the icon components directly
export const Ionicons = _Ionicons;
export const Feather = _Feather;

// ── Type helpers ─────────────────────────────────────────────────────────────
export type IoniconName = React.ComponentProps<typeof _Ionicons>["name"];
export type FeatherName  = React.ComponentProps<typeof _Feather>["name"];

// ── Ionicons name constants ───────────────────────────────────────────────────
/**
 * Typed constant map for every Ionicon used in the app.
 * Prevents typos and enables IDE auto-complete.
 */
export const IONICON = {
  // Actions
  ADD:                    "add"                     as IoniconName,
  ADD_CIRCLE_OUTLINE:     "add-circle-outline"      as IoniconName,
  ARROW_FORWARD:          "arrow-forward"           as IoniconName,
  CHECKMARK:              "checkmark"               as IoniconName,
  CHECKMARK_CIRCLE:       "checkmark-circle"        as IoniconName,
  CHECKMARK_CIRCLE_OUTLINE:"checkmark-circle-outline" as IoniconName,
  CHECKMARK_OUTLINE:      "checkmark-outline"       as IoniconName,
  CLOSE:                  "close"                   as IoniconName,
  CLOSE_CIRCLE:           "close-circle"            as IoniconName,
  CLOSE_OUTLINE:          "close-outline"           as IoniconName,
  COPY_OUTLINE:           "copy-outline"            as IoniconName,
  REFRESH_CIRCLE:         "refresh-circle"          as IoniconName,
  REFRESH_OUTLINE:        "refresh-outline"         as IoniconName,
  REMOVE:                 "remove"                  as IoniconName,

  // Auth & Security
  EYE:                    "eye"                     as IoniconName,
  EYE_OFF:                "eye-off"                 as IoniconName,
  LOCK_CLOSED:            "lock-closed"             as IoniconName,
  LOCK_OPEN:              "lock-open"               as IoniconName,
  SHIELD_CHECKMARK:       "shield-checkmark"        as IoniconName,
  SHIELD_CHECKMARK_OUTLINE:"shield-checkmark-outline" as IoniconName,

  // Commerce & Shopping
  CART:                   "cart"                    as IoniconName,
  CART_OUTLINE:           "cart-outline"            as IoniconName,
  EXPAND_OUTLINE:         "expand-outline"          as IoniconName,
  FLASH:                  "flash"                   as IoniconName,
  FLASH_OUTLINE:          "flash-outline"           as IoniconName,
  GIFT_OUTLINE:           "gift-outline"            as IoniconName,
  HEART:                  "heart"                   as IoniconName,
  HEART_OUTLINE:          "heart-outline"           as IoniconName,
  PRICETAG:               "pricetag"                as IoniconName,
  SPARKLES:               "sparkles"                as IoniconName,
  SPARKLES_OUTLINE:       "sparkles-outline"        as IoniconName,
  STAR:                   "star"                    as IoniconName,

  // Navigation & Layout
  CHEVRON_FORWARD:        "chevron-forward"         as IoniconName,
  FILTER_OUTLINE:         "filter-outline"          as IoniconName,
  GRID:                   "grid"                    as IoniconName,
  GRID_OUTLINE:           "grid-outline"            as IoniconName,
  LIST:                   "list"                    as IoniconName,

  // Logistics & Orders
  BARCODE_OUTLINE:        "barcode-outline"         as IoniconName,
  CAR:                    "car"                     as IoniconName,
  CAR_OUTLINE:            "car-outline"             as IoniconName,
  CUBE_OUTLINE:           "cube-outline"            as IoniconName,
  LOCATE_OUTLINE:         "locate-outline"          as IoniconName,
  LOCATION_OUTLINE:       "location-outline"        as IoniconName,
  RECEIPT_OUTLINE:        "receipt-outline"         as IoniconName,

  // Media & Visuals
  CAMERA:                 "camera"                  as IoniconName,
  CAMERA_OUTLINE:         "camera-outline"          as IoniconName,
  IMAGE_OUTLINE:          "image-outline"           as IoniconName,

  // People & Profile
  LOG_IN_OUTLINE:         "log-in-outline"          as IoniconName,
  PERSON:                 "person"                  as IoniconName,
  PERSON_CIRCLE_OUTLINE:  "person-circle-outline"   as IoniconName,
  PERSON_OUTLINE:         "person-outline"          as IoniconName,

  // Communication
  ALERT_CIRCLE:           "alert-circle"            as IoniconName,
  CHATBUBBLE_ELLIPSES:    "chatbubble-ellipses"     as IoniconName,
  MAIL:                   "mail"                    as IoniconName,
  MAIL_UNREAD:            "mail-unread"             as IoniconName,
  NOTIFICATIONS:          "notifications"           as IoniconName,
  NOTIFICATIONS_OUTLINE:  "notifications-outline"   as IoniconName,

  // Search & Discovery
  SEARCH:                 "search"                  as IoniconName,
  SEARCH_OUTLINE:         "search-outline"          as IoniconName,
  TRENDING_UP:            "trending-up"             as IoniconName,

  // Share & Social
  SHARE_OUTLINE:          "share-outline"           as IoniconName,
  SHARE_SOCIAL_OUTLINE:   "share-social-outline"    as IoniconName,

  // Tab Bar
  HOME:                   "home"                    as IoniconName,
  HOME_OUTLINE:           "home-outline"            as IoniconName,

  // Theme
  MOON_OUTLINE:           "moon-outline"            as IoniconName,
  SUNNY_OUTLINE:          "sunny-outline"           as IoniconName,

  // Time & Status
  TIME_OUTLINE:           "time-outline"            as IoniconName,

  // Misc
  TRASH_OUTLINE:          "trash-outline"           as IoniconName,
} as const;

// ── Feather name constants ────────────────────────────────────────────────────
/**
 * Typed constant map for every Feather icon used in the app.
 */
export const FEATHER = {
  CHECK:        "check"       as FeatherName,
  CHECK_CIRCLE: "check-circle" as FeatherName,
  EDIT_3:       "edit-3"      as FeatherName,
  MAXIMIZE_2:   "maximize-2"  as FeatherName,
  PACKAGE:      "package"     as FeatherName,
  ROTATE_CCW:   "rotate-ccw"  as FeatherName,
  SEARCH:       "search"      as FeatherName,
  TRASH_2:      "trash-2"     as FeatherName,
  X:            "x"           as FeatherName,
  ZAP:          "zap"         as FeatherName,
} as const;
