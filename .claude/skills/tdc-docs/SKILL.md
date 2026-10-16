---
name: tdc-docs
description: Create and maintain The Dreamer's Cave documentation. Use when updating README, CHANGELOG, API docs, component docs, or any documentation in docs/.
fork: true
---

# TDC Documentation Expert

Expert agent for creating and maintaining documentation for The Dreamer's Cave virtual music club website.

## Trigger

Use this skill when:
- User asks to create or update documentation
- User says "/docs", "/tdc-docs", or "/documentation"
- User asks to document an API endpoint, Vue component, or service
- User wants to update README, CHANGELOG, or API docs
- User asks to document location themes or design system

## Project Context

**The Dreamer's Cave** is a website for a virtual music club in Second Life, established in 2019.

**Domain:** thedreamerscave.club
**Motto:** "You Can See The Music"

### Project Structure

```
tdcweb/
├── backend/              # Flask REST API
│   ├── app/
│   │   ├── models/       # Database models (mysql-connector)
│   │   ├── routes/
│   │   │   ├── api/      # Public API endpoints
│   │   │   └── admin/    # Admin API endpoints
│   │   ├── services/     # Business logic (calendar, facebook, patreon)
│   │   ├── utils/        # Helpers, decorators, validators
│   │   └── tasks/        # Celery async tasks
│   ├── migrations/
│   └── tests/
├── frontend/             # Nuxt 4 (Vue 3 + TypeScript strict)
│   ├── app/              # Nuxt 4 app/ layer
│   │   ├── pages/        # File-based routes (SSG/ISR/SSR/SPA per routeRules)
│   │   ├── components/   # Vue components, flat naming via pathPrefix:false
│   │   ├── composables/  # useApiFetch, useAuth, useScrollAnimation, ...
│   │   ├── middleware/   # auth, admin, staff route guards
│   │   ├── utils/        # Pure helpers (auth-guard, etc.)
│   │   ├── plugins/      # gsap.client.ts, lenis.client.ts (client-only)
│   │   ├── stores/       # Pinia setup-syntax stores
│   │   ├── types/        # Shared TS types (api, user, location, event)
│   │   └── assets/css/   # Tailwind v4 + @theme + per-location vars
│   ├── server/           # Nitro BFF (auth handlers, revalidate, flaskFetch)
│   ├── i18n/locales/     # JSON: en.json, it.json, fr.json, es.json
│   └── tests/            # vitest + Playwright
├── apache/               # Production Apache vhost (Phase 6)
├── deploy/systemd/       # Production systemd units (Phase 6)
└── docs/                 # Documentation
```

### Tech Stack

**Backend:**
- Python 3.11+ / Flask 3
- MySQL 8.x with mysql-connector-python (NO SQLAlchemy)
- Celery + Redis (async tasks)
- JWT (PyJWT) + bcrypt + OAuth (Google, Discord, Facebook)

**Frontend:**
- Nuxt 4 (Vue 3 Composition API + TypeScript strict)
- Vite (under Nuxt)
- Tailwind CSS v4 (CSS-first @theme config) + per-location CSS vars
- GSAP + ScrollTrigger + Lenis (client-only, gsap.context+revert cleanup)
- Pinia (`@pinia/nuxt`, setup-syntax stores)
- @nuxtjs/i18n (`prefix_except_default` EN/IT/FR/ES)
- @nuxtjs/seo + sitemap + robots (Schema.org JSON-LD via useSchemaOrg)
- TipTap (admin-only, inside `<ClientOnly>`)
- vee-validate + zod (type-safe validation)

**External Integrations:**
- Google Calendar (staff + public calendars)
- Facebook (page + group auto-posting)
- Patreon (supporter tiers, exclusive content)
- Second Life API (in-world display panels)

### Database Tables

Core entities:
- `users`, `oauth_accounts` - User authentication
- `locations`, `location_translations` - Club venues with theming
- `artists`, `artist_translations` - Performer profiles
- `events`, `event_translations`, `event_artists` - Event management
- `blog_posts`, `blog_post_translations` - News/blog
- `media` - Media library
- `patreon_tiers`, `patreon_supporters`, `exclusive_content` - Patreon integration
- `notification_queue`, `user_notification_preferences` - Email notifications
- `integration_settings`, `integration_logs` - External service configs

### Location Theming System

Each location has a unique visual identity (see `docs/plans/dreamers_cave_locations_mood_guide.md`):

| Location | Category | Primary Color | Mood |
|----------|----------|---------------|------|
| The Dreamer's Cave | Cosmic/Tech | #0891b2 (cyan) | Immersive, hexagonal, cosmic |
| DreamVision | Cosmic/Tech | #06b6d4 (cyan) | 360°, explosive, monumental |
| Evanescence | Cosmic/Tech | #fbbf24 (gold) | Transcendent, portal |
| The Lounge | Hybrid | #a855f7 (purple) | Brutalist, Berlin club |
| Live Magic | Hybrid | #dc2626 (red) | Space station, fire |
| Noah's Ark | Warm/Intimate | #d97706 (amber) | Fairy tale, wooden ship |
| Jazz Club | Warm/Intimate | #92400e (brown) | Speakeasy, 1920s |
| Arquipélago | Warm/Intimate | #14b8a6 (teal) | Tropical, bioluminescent |

## Instructions

### Phase 1: Identify What to Document

```bash
# Check current state
git status
git log --oneline -5

# Find existing docs
find . -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" | head -20

# Check what changed recently
git diff --name-only HEAD~3..HEAD 2>/dev/null
```

### Phase 2: Documentation Structure

```
/docs/
├── api/
│   ├── public-api.md         # Public REST API endpoints
│   ├── admin-api.md          # Admin API endpoints
│   ├── sl-api.md             # Second Life integration API
│   └── authentication.md     # Auth flow (JWT, OAuth)
├── frontend/
│   ├── components.md         # Vue component reference
│   ├── composables.md        # Composition API hooks
│   ├── animations.md         # GSAP scroll animation guide
│   └── theming.md            # Location theme system
├── integrations/
│   ├── google-calendar.md    # Calendar sync setup
│   ├── facebook.md           # Facebook posting
│   └── patreon.md            # Patreon webhooks
├── database/
│   └── schema.md             # Database tables and relations
├── deployment/
│   ├── server.md             # Production deployment
│   └── development.md        # Local dev setup
└── i18n/
    └── translations.md       # Translation workflow
```

### Phase 3: API Documentation Format

For backend endpoints:

```markdown
## Endpoint Name

`METHOD /api/v1/path`

Description of what this endpoint does.

### Authentication

`Authorization: Bearer <jwt_token>` or Session cookie

### Request

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | JWT token or session |
| Accept-Language | No | Preferred language (en, it, fr, es) |

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| lang | string | Override response language |

**Body:**
```json
{
    "title": "Event title",
    "location_id": 1
}
```

### Response

**Success (200):**
```json
{
    "success": true,
    "data": {...},
    "meta": {
        "pagination": {...}
    }
}
```

**Errors:**
| Code | Error | Description |
|------|-------|-------------|
| 401 | Unauthorized | Invalid or expired token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not found | Resource doesn't exist |
```

### Phase 4: Vue Component Documentation Format

```markdown
# ComponentName

## Overview

Brief description of what this component does.

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| location | Object | Yes | - | Location data with theme |
| animated | Boolean | No | true | Enable GSAP animations |

## Emits

| Event | Payload | Description |
|-------|---------|-------------|
| select | location_id | Emitted when location selected |

## Slots

| Slot | Description |
|------|-------------|
| default | Main content |
| header | Custom header |

## Usage

```vue
<LocationCard
  :location="location"
  :animated="true"
  @select="handleSelect"
>
  <template #header>
    <h3>{{ location.name }}</h3>
  </template>
</LocationCard>
```

## Theming

Uses location CSS variables:
- `--color-primary`: Main accent color
- `--color-secondary`: Secondary color
- `--gradient-hero`: Background gradient

## Animation

Uses GSAP ScrollTrigger for entrance animation.
See `composables/useScrollAnimations.js` for implementation.
```

### Phase 5: Composable Documentation Format

```markdown
# useComposableName

## Overview

What this composable provides.

## Usage

```javascript
import { useScrollAnimations } from '@/composables/useScrollAnimations'

const { initSmoothScroll, animateHero, animateReveal } = useScrollAnimations()
```

## Returns

| Property | Type | Description |
|----------|------|-------------|
| initSmoothScroll | Function | Initialize Lenis smooth scroll |
| animateHero | Function | Hero section parallax animation |
| animateReveal | Function | Staggered reveal animation |

## Functions

### initSmoothScroll()

Initializes Lenis smooth scrolling. Call once on app mount.

### animateHero(element)

Creates parallax effect on hero section.

**Parameters:**
- `element`: HTMLElement - The hero container

### animateReveal(elements, options?)

Staggered reveal animation on scroll.

**Parameters:**
- `elements`: HTMLElement[] - Elements to animate
- `options`: Object - ScrollTrigger options

## Example

```javascript
onMounted(() => {
  initSmoothScroll()
  animateHero(heroRef.value)
  animateReveal(document.querySelectorAll('.card'))
})
```
```

### Phase 6: Integration Documentation Format

```markdown
# Integration Name

## Overview

What this integration does and why.

## Setup

### 1. Create Credentials

Steps to create API credentials...

### 2. Configure Environment

```env
INTEGRATION_API_KEY=your-key
INTEGRATION_SECRET=your-secret
```

### 3. Enable in Admin

Navigate to Admin > Integrations > Enable...

## Usage

### Automatic Sync

How automatic syncing works...

### Manual Trigger

How to trigger manually from admin...

## Webhook Handling

For Patreon/Facebook webhooks:

| Event | Handler | Description |
|-------|---------|-------------|
| members:pledge:create | _handle_new_pledge | New supporter |

## Troubleshooting

Common issues and solutions...
```

### Phase 7: Translation Documentation

```markdown
# i18n Translation Guide

## File Structure

```
frontend/src/i18n/
├── en.json    # English (default)
├── it.json    # Italian
├── fr.json    # French
├── es.json    # Spanish
└── index.js   # i18n setup
```

## Adding Translations

1. Add key to `en.json` (source of truth)
2. Add translations to other language files
3. Use in components:

```vue
<template>
  <h1>{{ $t('locations.title') }}</h1>
</template>
```

## Content Translations (Database)

Content from database uses `*_translations` tables:
- `location_translations`
- `event_translations`
- `artist_translations`
- `blog_post_translations`

Query with language parameter:
```python
def get_location(slug, lang='en'):
    # Returns location with translation for specified language
```
```

### Phase 8: Git Workflow

After documentation updates:

1. **Review changes:**
   ```bash
   git status && git diff
   ```

2. **Stage docs:**
   ```bash
   git add README.md CHANGELOG.md docs/
   ```

3. **Commit:**
   ```bash
   git commit -m "docs: [description]

   - Specific changes made

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

4. **Push (only if explicitly requested)**

### Phase 9: Report

```markdown
## Documentation Update Complete

### Files Created:
- docs/api/public-api.md (new)
- docs/frontend/animations.md (new)

### Files Updated:
- README.md
- CHANGELOG.md

### Recommendations:
- Document remaining API endpoints
- Add more component examples
- Complete integration guides
```

## Important Notes

- ALL documentation and code comments MUST be in English
- Content translations (for users) are in the database
- Keep examples practical and runnable
- Reference actual code paths (e.g., `frontend/src/components/locations/LocationCard.vue:45`)
- Include location theming context where relevant
- Document GSAP animations with visual descriptions
- Update CHANGELOG.md for significant doc changes
- Only push if user explicitly requests
- Consider both web developers and content editors as audiences
