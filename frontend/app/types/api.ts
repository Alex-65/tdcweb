/**
 * Shared API response shapes.
 *
 * Keep these stable — many pages / composables reference ApiResponse<T>
 * and ApiError. Fields are a minimal subset that covers most Flask
 * responses; extend per-module types when needed.
 */

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ApiResponse<T> {
  data: T
  meta?: {
    page?: number
    per_page?: number
    total?: number
  }
}
