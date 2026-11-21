# Decisions

## 2026-11-21 — Rejected auto-scrape + auto-connect design
- Original idea: scrape web/social data about people in a GPS region, then
  auto-follow/auto-connect with them on social platforms.
- Why rejected: violates every major platform's ToS (LinkedIn, Instagram, X),
  risks account bans and legal exposure (GDPR/CCPA-style privacy law,
  hiQ v. LinkedIn precedent on scraping), and is the exact pattern that got
  Clearview AI sued/banned in multiple countries.
- Chose instead: enrich *place/public-entity* data (via OSM/Overpass, later
  Google Places/Eventbrite) + match only against NearbyConnect's own
  opted-in users. Connections are suggested, not automated — user taps
  "Connect," other user approves.

## 2026-11-21 — Chose OpenStreetMap/Overpass over Google Places for v1
- Options: Google Places API, Overpass API (OSM), Foursquare
- Chose: Overpass API
- Why: free, no API key needed to start, good coverage for most places
- Downside: data quality/completeness varies by region vs. Google Places;
  swap in Google Places later once we have API keys and the matching logic
  is proven

## 2026-11-21 — Chose FastAPI + Python for backend
- Options: FastAPI (Python), Express (Node), Django
- Chose: FastAPI
- Why: user already knows Python (CS student), FastAPI is fast to write and
  has built-in request validation (useful for a beginner avoiding bad input)
- Downside: less familiar than Django's "batteries included" style, but
  simpler for a small API-only backend

## 2026-11-21 — SQLAlchemy with SQLite by default, PostgreSQL via DATABASE_URL
- Options: PostgreSQL only, SQLite only, SQLAlchemy supporting both
- Chose: SQLAlchemy; SQLite file by default, set DATABASE_URL for PostgreSQL
- Why: tests and first runs need zero setup (no DB password), while the
  same code runs on PostgreSQL later. pgvector/embeddings are still deferred
  (scoring uses keyword overlap first, per PLAN step 6).
- Downside: no migrations tool yet. If a table changes, delete
  nearbyconnect.db (dev only) or add Alembic before real data exists.

## 2026-11-21 — Simple bearer-token login
- Options: no auth, simple random token, full OAuth / email+password
- Chose: random token issued at sign-up; only its SHA-256 hash is stored
- Why: Phase 2 shares location-derived info and connect requests, so
  "anyone can act as anyone" is not acceptable even in v1. Full auth is
  more than a beginner v1 needs.
- Downside: lose the token = lose the account (no recovery yet).

## 2026-11-21 — No "new match nearby" push notifications
- Options: background location + push on match; server scans for new
  matches whenever anyone updates location; no match pushes
- Chose: no match pushes. Push only for connect request / accepted
- Why: background tracking breaks the "only while the app is open"
  promise; server-side scanning would tell people when someone with
  their interests is near, a presence leak, and is spammy
- Revisit only with an explicit, separate opt-in and rate limits

## 2026-11-21 — Keep OSM/Overpass; backup providers noted
- Public Overpass servers were overloaded during development.
- If that persists: add Geoapify (same OSM data, reliable servers, free key)
  or Foursquare Places (better networking-style categories, free tier).
  Both can return the same {name, type, lat, lon} shape as osm_client.
