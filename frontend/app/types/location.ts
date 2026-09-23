/**
 * Location (venue) types.
 *
 * TDC has 10+ themed locations grouped into three moods
 * (Cosmic/Tech, Hybrid, Warm/Intimate) per CLAUDE.md § Location Theming.
 * The `slug` field is the authoritative identifier used by
 * useLocationTheme(slug) to drive CSS variables in app/assets/css/main.css.
 */

export type LocationMood = 'cosmic' | 'hybrid' | 'warm'

export interface Location {
  id: number
  slug: string
  name: string
  mood: LocationMood
  capacity: number
  hero_image: string | null
  description: string | null
  created_at: string
}
