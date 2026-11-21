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
