/**
 * auth-forward — Nitro server middleware.
 *
 * Runs on every incoming server request (page render, server route, static).
 * Reads the `tdc_access` HttpOnly cookie; if present, stamps
 * `event.context.flaskHeaders = { Authorization: 'Bearer <jwt>' }` so that
 * downstream `flaskFetch(url, event)` calls (see server/utils/flask-client.ts)
 * authenticate against Flask on behalf of the user.
 *
 * When the cookie is absent (guest request) we leave `flaskHeaders`
 * undefined. `flaskFetch` defaults to an empty headers object in that case,
 * and Flask handlers gated with @jwt_required will reject with 401 as
 * expected.
 *
 * Contract (do NOT change without updating flaskFetch and Flask in lockstep):
 *   - Cookie name: exactly `tdc_access`
 *   - Header key:  exactly `Authorization` (capital A — case-insensitive per
 *     HTTP spec, but Flask's default JWT extractor and our tests rely on this
 *     casing)
 *   - Header value: exactly `Bearer <jwt>` (capital B, single space, no
 *     surrounding whitespace)
 *
 * Implementation note: `getCookie` and `defineEventHandler` are looked up
 * on `globalThis` at handler-invocation time (never at module-eval time).
 * Rationale: (1) ESM hoists `import` statements above top-level test-file
 * stubs, so a bare auto-import identifier at module scope throws
 * ReferenceError in vitest; (2) Nitro's prod bundle actually *does* expose
 * these on globalThis in some code paths, but for robustness we also fall
 * back to a direct `h3` import. This mirrors the call-time lookup used in
 * server/utils/flask-client.ts.
 *
 * Related: CLAUDE.md § Project Constants (cookie names/lifetimes),
 * docs/frontend/nuxt-playbook.md §11.3, spec §8.2–§8.3.
 */
import type { H3Event, EventHandler } from 'h3'
import {
  defineEventHandler as h3DefineEventHandler,
  getCookie as h3GetCookie,
} from 'h3'
import { TDC_ACCESS_COOKIE } from '../utils/cookies'

type DefineEventHandlerFn = <T extends EventHandler>(handler: T) => T
type GetCookieFn = (event: H3Event, name: string) => string | undefined

const resolveDefineEventHandler = (): DefineEventHandlerFn => {
  const stubbed = (globalThis as unknown as { defineEventHandler?: DefineEventHandlerFn })
    .defineEventHandler
  return stubbed ?? (h3DefineEventHandler as DefineEventHandlerFn)
}

const resolveGetCookie = (): GetCookieFn => {
  const stubbed = (globalThis as unknown as { getCookie?: GetCookieFn }).getCookie
  return stubbed ?? (h3GetCookie as GetCookieFn)
}

const handler: EventHandler = ((event: H3Event) => {
  const access = resolveGetCookie()(event, TDC_ACCESS_COOKIE)
  if (access) {
    event.context.flaskHeaders = { Authorization: `Bearer ${access}` }
  }
}) as EventHandler

// Lazy wrap: resolve defineEventHandler at first *invocation*, not at
// module-eval time, so ESM-hoisted imports in vitest don't see `undefined`.
// In prod, the h3 import is always available; in tests, the globalThis stub
// (installed by the test file before its own import statement) takes
// precedence.
let _wrapped: EventHandler | null = null
const wrapped: EventHandler = ((event: H3Event) => {
  if (!_wrapped) {
    _wrapped = resolveDefineEventHandler()(handler)
  }
  return _wrapped(event)
}) as EventHandler

export default wrapped
