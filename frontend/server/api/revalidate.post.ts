import { defineEventHandler } from 'h3'
import { z } from 'zod'
import type { ApiResponse } from '~/types/api'
import type { User } from '~/types/user'

/**
 * POST /api/revalidate -- admin-gated on-demand SSR cache invalidation.
 *
 * Auth model: caller must be authenticated as `admin`. We piggyback on the
 * auth-forward middleware (server/middleware/auth-forward.ts) which has
 * already attached the `tdc_access` HttpOnly cookie as `Authorization:
 * Bearer ...` on `event.context.flaskHeaders`. We then ask Flask "who am I"
 * via /api/auth/me and inspect role. Two failure modes:
 *   - flaskFetch throws (no/expired/invalid cookie)         -> 401
 *   - role !== 'admin' (logged in as user/staff)            -> 403
 *
 * Body: { path: string }. Hardened beyond the spec sketch:
 *   - must start with '/'
 *   - no '..'  (path traversal)
 *   - no '//'  (ambiguous routing -- could match unintended cache entries)
 *   - max 500 chars (sanity bound)
 *   - non-empty (zod min(1) implicit via the regex)
 *
 * Cache invalidation: Nitro stores SWR/cached route entries under storage
 * keys of the form (after unstorage normalization):
 *   cache:nitro:routes:_:<escapedPathname>.<hash>.json
 * where <escapedPathname> is `escapeKey(decodeURI(pathname))` (strips \W,
 * truncated to 16 chars) and <hash> is a content hash of the full request
 * URL including query string. Source: nitropack/dist/runtime/internal/
 * cache.mjs lines 29 and 137-145, group default `nitro/routes` set in
 * runtime/internal/app.mjs line 131. The on-disk layout
 * `.nuxt/cache/nitro/routes/_/<pathname>.<hash>.json` confirms this.
 *
 * Because we don't know the hash suffix at revalidate time (and there may
 * be multiple entries per path -- different query strings, different
 * `varies` headers), we list keys under the per-path prefix and remove
 * each match. This is precise (no neighbouring paths affected) and
 * observable in tests. If Nitro changes its key format, the handler
 * silently no-ops -- the worst case is staleness until next SWR tick,
 * never wrong content.
 *
 * Response shape: 200 { revalidated: <path> }. Note this endpoint does
 * NOT use the Flask `{success, data}` envelope -- the envelope is a Flask
 * convention for /api/* proxied to backend, not a Nitro-internal contract.
 * Treating revalidate as a Nitro internal endpoint keeps it free of an
 * envelope wrapper that would only confuse client-side callers.
 *
 * Spec: docs/superpowers/specs/2026-04-23-nuxt-integration-design.md
 *       sec 7.3.
 * Plan: docs/superpowers/plans/2026-04-23-nuxt-integration.md Task 4.3.
 */

const PATH_TRAVERSAL = /\.\./
const DOUBLE_SLASH = /\/\//
const ESCAPE_NON_WORD = /\W/g

const revalidateSchema = z.object({
  path: z
    .string()
    .min(1, 'Path is required')
    .max(500, 'Path must be 500 chars or fewer')
    .refine((p) => p.startsWith('/'), 'Path must start with /')
    .refine((p) => !PATH_TRAVERSAL.test(p), 'Path must not contain ".."')
    .refine((p) => !DOUBLE_SLASH.test(p), 'Path must not contain "//"'),
})

// Mirror nitropack's escapeKey(): strips non-word chars from the pathname,
// truncates to 16 chars (or "index" for the empty case after stripping).
const encodePathname = (path: string): string => {
  // path always begins with '/' (validated above); decodeURI handles UTF-8
  // pathnames consistently with what Nitro will have stored.
  const pathname = decodeURI(path.split('?')[0] ?? path)
  const stripped = pathname.replace(ESCAPE_NON_WORD, '').slice(0, 16)
  return stripped || 'index'
}

export default defineEventHandler(async (event) => {
  // 1. Admin gate. /api/auth/me returns ApiResponse<User> per
  //    backend/app/routes/api/auth.py: `success(g.current_user.to_dict())`.
  //    A throw means missing/invalid Bearer (401); a non-admin role means
  //    403. We do NOT leak which of the two it was beyond the status code.
  let me: ApiResponse<User>
  try {
    me = await flaskFetch<ApiResponse<User>>('/api/auth/me', event)
  }
  catch {
    throw createError({ statusCode: 401, statusMessage: 'Not authenticated' })
  }
  if (me.data.role !== 'admin') {
    throw createError({ statusCode: 403, statusMessage: 'Admin role required' })
  }

  // 2. Validate body. zod's parser raises on bad input; we surface the
  //    first issue's message as a 400. This is a Nitro internal endpoint,
  //    not a Flask-style API, so no envelope on the error either.
  const body = await readValidatedBody(event, (input) => {
    const result = revalidateSchema.safeParse(input)
    if (!result.success) {
      const message = result.error.issues[0]?.message ?? 'Invalid path'
      throw createError({ statusCode: 400, statusMessage: message })
    }
    return result.data
  })

  // 3. Clear matching cache entries. See header comment for key format.
  const encoded = encodePathname(body.path)
  const storage = useStorage('cache:nitro:routes')
  // Within this mounted storage, keys lose the `cache:nitro:routes:`
  // prefix; the actual key is `_:<encoded>.<hash>.json`. We list under
  // `_` (the default group `name`) and filter by encoded prefix. This is
  // robust against future Nitro key-format tweaks: if no keys match, we
  // still 200 -- nothing to invalidate is not an error.
  const allKeys = await storage.getKeys('_')
  const prefix = `_:${encoded}.`
  const matching = allKeys.filter((k) => k.startsWith(prefix))
  await Promise.all(matching.map((k) => storage.removeItem(k)))

  return { revalidated: body.path }
})
