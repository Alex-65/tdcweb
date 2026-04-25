# TDC Production Deployment Runbook

Deployment of The Dreamer's Cave to mioh1 (Hetzner Frankfurt, Ubuntu).
This runbook is the definitive source for putting Phase 4-6 work into
production. It supersedes any pre-Nuxt deployment notes.

**Audience:** ops engineer with sudo access to mioh1.
**Scope:** first-time install AND subsequent re-deployments.
**Domain:** thedreamerscave.club (alias www.thedreamerscave.club).
**Cert:** unified-cert (Let's Encrypt SAN, auto-renewed by certbot).

---

## 1. Topology

```
   Internet --> :443 Apache (TLS, unified-cert)
                  |
                  +--> /_nuxt/, /favicon.ico    --> static disk
                  +--> /api/auth/**             --> :9501 Nuxt (BFF)
                  +--> /api/revalidate          --> :9501 Nuxt (BFF)
                  +--> /api/**  (other)         --> :9500 Flask
                  +--> /trullo                  --> :3600 (legacy ext)
                  +--> /                        --> :9501 Nuxt (SSR/SSG/SPA)

   :9501  tdcweb-frontend.service  (node SSR, www-data)
   :9500  tdcweb-backend.service   (gunicorn Flask, www-data)
   :3306  mysql                     (existing)
   :6379  redis                     (existing)
```

Both backend processes bind 127.0.0.1; only Apache (and the colocated
Nuxt node, via flaskFetch) can reach Flask. No direct internet access.

---

## 2. Prerequisites

- [ ] Apache modules: `proxy proxy_http headers rewrite ssl`
  ```bash
  sudo a2enmod proxy proxy_http headers rewrite ssl
  ```
- [ ] Node.js >= 20 (Nuxt 4 requirement). Verify: `node --version`.
- [ ] Python >= 3.11. Verify: `python3 --version`.
- [ ] MySQL 8.x with `tdcweb` database + `tdcweb` user, full schema applied.
- [ ] Redis 6+ on :6379.
- [ ] unified-cert at `/etc/letsencrypt/live/unified-cert/` covering
      `thedreamerscave.club` AND `www.thedreamerscave.club`. Verify:
  ```bash
  sudo openssl x509 -in /etc/letsencrypt/live/unified-cert/cert.pem \
       -noout -text | grep -A 1 "Subject Alternative Name"
  ```
- [ ] webroot for ACME challenges: `/var/www/acme/.well-known/acme-challenge/`
      (writable by certbot, readable by Apache).

---

## 3. Production secrets (one-time)

Two env files live OUTSIDE the repo. Owner `root`, group `www-data`,
mode `0640`. The systemd units load them via `EnvironmentFile=`.

### 3.1 `/etc/tdcweb/backend.env`

```bash
sudo install -d -m 0750 -o root -g www-data /etc/tdcweb
sudo tee /etc/tdcweb/backend.env > /dev/null <<'EOF'
FLASK_ENV=production

# Required (ProductionConfig raises KeyError at import without these).
# Generate fresh with: python3 -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=<replace>
JWT_SECRET_KEY=<replace>

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tdcweb
DB_USER=tdcweb
DB_PASSWORD=<real prod password>
DB_POOL_SIZE=20

# Cache + tasks
REDIS_URL=redis://localhost:6379/0

# OAuth (fill as integrations come online; OK to leave blank pre-launch)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=

# Email (iRedMail, self-hosted)
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=noreply@thedreamerscave.club
MAIL_PASSWORD=<replace>
MAIL_DEFAULT_SENDER=noreply@thedreamerscave.club

# Application
BASE_URL=https://thedreamerscave.club
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,it,fr,es

# File uploads
UPLOAD_FOLDER=/data1/tdcweb/uploads
MAX_CONTENT_LENGTH=16777216
EOF
sudo chown root:www-data /etc/tdcweb/backend.env
sudo chmod 0640 /etc/tdcweb/backend.env
```

### 3.2 `/etc/tdcweb/frontend.env`

```bash
sudo tee /etc/tdcweb/frontend.env > /dev/null <<'EOF'
# Required: SSR-side base URL for Flask (called by useApiFetch on SSR
# and by the BFF flaskFetch helper). TD-014 closure: without this,
# resolveApiBaseURL throws at first SSR fetch.
NUXT_FLASK_URL=http://127.0.0.1:9500

# Required: opaque server-only secret for cookie signing.
# Generate with: python3 -c 'import secrets; print(secrets.token_hex(32))'
NUXT_COOKIE_SECRET=<replace>

# Public (sent to client; safe).
NUXT_PUBLIC_SITE_URL=https://thedreamerscave.club
NUXT_PUBLIC_API_BASE=/api
EOF
sudo chown root:www-data /etc/tdcweb/frontend.env
sudo chmod 0640 /etc/tdcweb/frontend.env
```

---

## 4. First-time install

### 4.1 Code on disk

```bash
# Production tree at /data1/tdcweb (NOT /data1/tdcweb-dev).
sudo mkdir -p /data1/tdcweb
sudo chown -R deploy:www-data /data1/tdcweb
git clone git@github.com:Alex-65/tdcweb.git /data1/tdcweb
cd /data1/tdcweb
git checkout main  # or the prod tag, e.g. v1.0.0
```

### 4.2 Backend setup

```bash
cd /data1/tdcweb/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
deactivate
```

### 4.3 Frontend build

```bash
cd /data1/tdcweb/frontend
npm ci --omit=dev
NUXT_PUBLIC_SITE_URL=https://thedreamerscave.club \
NUXT_PUBLIC_API_BASE=/api \
  npm run build
# Verify .output/ exists.
ls .output/server/index.mjs
ls .output/public/_nuxt/
```

### 4.4 systemd units

```bash
sudo cp /data1/tdcweb/deploy/systemd/tdcweb-backend.service \
        /etc/systemd/system/tdcweb-backend.service
sudo cp /data1/tdcweb/deploy/systemd/tdcweb-frontend.service \
        /etc/systemd/system/tdcweb-frontend.service
sudo systemctl daemon-reload
sudo systemctl enable tdcweb-backend tdcweb-frontend
sudo systemctl start tdcweb-backend
sudo systemctl status tdcweb-backend  # green
sudo systemctl start tdcweb-frontend
sudo systemctl status tdcweb-frontend  # green
# Smoke:
curl -s http://127.0.0.1:9500/api/health | head
curl -s http://127.0.0.1:9501/ | grep -c "You Can See The Music"
```

If either service fails to start, `journalctl -u tdcweb-backend -n 50`
or `journalctl -u tdcweb-frontend -n 50` shows the cause. Most common:
missing env var (loud KeyError for `SECRET_KEY`/`JWT_SECRET_KEY`) or
build artifact missing.

### 4.5 Apache vhost swap

```bash
# Stop the legacy static-content vhost.
sudo a2dissite 000-thedreamerscave thedreamerscave-ssl

# Symlink the new Nuxt-aware vhost.
sudo ln -s /data1/tdcweb/apache/thedreamerscave-prod.conf \
           /etc/apache2/sites-available/thedreamerscave-prod.conf
sudo a2ensite thedreamerscave-prod

# Validate + reload.
sudo apache2ctl configtest
sudo systemctl reload apache2
```

If `apache2ctl configtest` complains, fix BEFORE reload. Apache will
keep the previous config running until you reload.

### 4.6 First-request smoke

From your laptop (NOT the server):

```bash
# Public landing renders + has correct title.
curl -s https://thedreamerscave.club/ | grep -c "You Can See The Music"
# expected: >= 1

# Italian locale renders.
curl -s https://thedreamerscave.club/it/ | grep -c "Puoi vedere la musica"
# expected: >= 1

# Health endpoint (Flask).
curl -s https://thedreamerscave.club/api/health | head

# Locations endpoint (Flask, enveloped).
curl -s https://thedreamerscave.club/api/locations | head

# BFF login (Nuxt, expect 401 because no creds).
curl -s -X POST https://thedreamerscave.club/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"x","password":"y"}' | head
# expected: enveloped error, 401
```

---

## 5. Re-deploy (subsequent releases)

```bash
cd /data1/tdcweb
git pull --ff-only
git checkout <release-tag>

# Backend deps (only if requirements.txt changed)
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Frontend rebuild
cd ../frontend
npm ci --omit=dev
NUXT_PUBLIC_SITE_URL=https://thedreamerscave.club \
NUXT_PUBLIC_API_BASE=/api \
  npm run build

# Restart services (use restart, not reload, so node reloads .output/).
sudo systemctl restart tdcweb-backend
sudo systemctl restart tdcweb-frontend

# Apache reload (only if vhost changed; usually not).
sudo apache2ctl configtest && sudo systemctl reload apache2

# Re-run section 4.6 smoke tests.
```

---

## 6. Rollback

If a release is bad:

```bash
cd /data1/tdcweb
git checkout <previous-tag>
cd frontend && npm ci --omit=dev && npm run build && cd ..
sudo systemctl restart tdcweb-backend tdcweb-frontend
```

If Apache vhost changed and is the cause, restore the previous vhost
file from git history and reload. The legacy `000-thedreamerscave.conf`
+ `thedreamerscave-ssl.conf` are NOT in the repo; preserve copies in
`/root/backup-pre-nuxt/` before swap.

---

## 7. Observability

- **Apache logs:** `/var/log/apache2/thedreamerscave-{ssl-,}{access,error}.log`
- **Flask logs:** `journalctl -u tdcweb-backend -f`
- **Nuxt logs:** `journalctl -u tdcweb-frontend -f`
- **MySQL slow query:** `/var/log/mysql/mysql-slow.log` (if enabled)
- **Cert expiry:** `sudo certbot certificates` (unified-cert auto-renews
  via systemd timer; verify `systemctl list-timers | grep certbot`)

---

## 8. Cert renewal

unified-cert is renewed automatically by certbot. Verification:

```bash
sudo certbot renew --dry-run
```

The renewal hook should reload Apache so the new cert takes effect.
Verify the deploy hook is set:

```bash
ls /etc/letsencrypt/renewal-hooks/deploy/
# expected: a script that runs `systemctl reload apache2`
```

---

## 9. Known gotchas

- **Nuxt build caches `.nuxt/cache/`.** If a deploy seems to serve
  stale SSR HTML on `/events` or `/blog` (the SWR-cached routes),
  `rm -rf /data1/tdcweb/frontend/.nuxt/cache/` and restart the
  frontend service.

- **`NUXT_FLASK_URL` MUST be set** before the frontend service starts.
  The `resolveApiBaseURL` helper in `useApiFetch` throws at first SSR
  fetch otherwise (every public page 500s). TD-014 in TECH_DEBT.md
  closes once this runbook is committed and the env file is on prod.

- **devProxy is NOT in production.** Apache routes `/api/auth/**` and
  `/api/revalidate` to Nuxt, all other `/api/**` to Flask. The Nuxt
  `routeRules.proxy` block in `nuxt.config.ts` is dev-only (and
  inactive in prod because the `/api/**` requests never reach the
  Nuxt node -- Apache catches them first).

- **Apache `/api/auth/` and `/api/revalidate` MUST be declared
  before `/api/`.** Apache evaluates `<Location>` blocks in source
  order; the more specific path must appear first.

---

## 10. References

- Apache vhost: `apache/thedreamerscave-prod.conf`
- systemd units: `deploy/systemd/tdcweb-{backend,frontend}.service`
- Architecture: `docs/superpowers/specs/2026-04-23-nuxt-integration-design.md`
- Project plan: `docs/plans/pdp-v3.md`
- Phase 4 patterns (envelope, BFF, cookies): `.claude/agents/tdc-frontend-expert.md`
