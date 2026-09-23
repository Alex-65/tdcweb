/**
 * Shared API response shapes.
 *
 * Mirrors the Flask `app.utils.responses` envelope contract:
 *   Success: { success: true, data: <T>, meta?: {...} }
 *   Error:   { success: false, error: <message>, errors?: {...} }
 *
 * Backend convention is enforced project-wide: every Flask endpoint MUST
 * use `responses.success()` / `responses.error()`. Frontend BFF handlers
 * unwrap `.data` before re-shaping for client consumption (see
 * server/api/auth/*.ts). Direct-to-Flask client calls (e.g. via Apache
 * devProxy for /api/locations) receive the envelope as-is and must
 * unwrap accordingly.
 */

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ApiResponse<T> {
  success: true
  data: T
  meta?: {
    page?: number
    per_page?: number
    total?: number
  }
}

export interface ApiErrorResponse {
  success: false
  error: string
  errors?: Record<string, string[]>
}
