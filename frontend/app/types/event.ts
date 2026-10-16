/**
 * Event types.
 *
 * Event lifecycle statuses match pdp-v2 §3.1 events table constraints.
 * `location_id` references Location.id. `starts_at` / `ends_at` are
 * ISO 8601 strings serialized by Flask — we keep them as `string` here
 * and format at the component layer (SSR-safe per CLAUDE.md § SSR
 * Client-Only Rules: no `new Date().toLocaleString()` in templates).
 */

export type EventStatus = 'draft' | 'scheduled' | 'live' | 'ended' | 'cancelled'

export interface Event {
  id: number
  slug: string
  title: string
  location_id: number
  starts_at: string
  ends_at: string
  status: EventStatus
  description: string | null
  poster_image: string | null
}
