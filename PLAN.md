# Plan: NearbyConnect (v1 — Location-based opportunity/people feed)

## Goal
Given a GPS point, return a ranked list of nearby places/opportunities that
match the user's stated interests, using only free/legal data sources —
no scraping of individuals, no automated social actions.

## Phase 1 — Backend core (build first, test via terminal/Postman, no app UI yet)

- [x] 1. Project skeleton
      Files: src/backend/main.py, src/backend/requirements.txt
      Do: minimal FastAPI app with a GET /health endpoint
      Check: `uvicorn main:app --reload` runs, curl localhost:8000/health returns {"status":"ok"}
      Done 2026-11-21: tested with curl, got {"status":"ok"}

- [x] 2. Location input endpoint
      Files: src/backend/routers/location.py
      Do: POST /nearby accepting {lat, lon, radius_m}; validate ranges
      Check: invalid lat/lon (e.g. lat=200) returns 422, valid input returns 200
      Done 2026-11-21: 8 pytest tests pass (src/backend/tests/test_location.py);
      curl confirmed 200 for valid input, 422 for lat=200. radius_m defaults
      to 1000, max 5000. Coordinates are not logged.

- [x] 3. Place data fetch (Overpass/OSM)
      Files: src/backend/services/osm_client.py
      Do: given lat/lon/radius, call Overpass API, return raw list of nearby
          places (name, type, coordinates)
      Check: unit test with a known lat/lon (e.g. a landmark) returns >0 places
      Done 2026-11-21: 10 offline tests pass (fake server). Live test
      (`pytest -m network`) passed on retry (46 s). Public Overpass servers
      are slow/flaky (504/502/timeouts seen), so the client tries 3 servers.

- [x] 4. Data cleaning + validation
      Files: src/backend/services/clean.py
      Do: dedupe places, drop entries missing a name, normalize place "type"
          into a small fixed category set (food, coworking, event space, etc.)
      Check: test with deliberately messy/duplicate input, confirm output is
          deduped and categorized
      Done 2026-11-21: 14 tests in tests/test_clean.py pass. Drops blank names
      and bad coords, tidies names, dedupes by OSM id or same name within 50 m,
      maps tags to 11 categories (food, cafe, coworking, education,
      event_space, culture, outdoors, fitness, shopping, office, other).

- [x] 5. User interest profile (minimal)
      Files: src/backend/models/user.py, src/backend/routers/profile.py
      Do: user can POST a list of interest tags (e.g. ["AI", "startups"])
      Check: POST then GET returns the same tags
      Done 2026-11-21: 10 tests in tests/test_profile.py pass. POST /users
      (sign-up, returns a token once), GET /me, PUT + GET /me/interests
      (PUT = replace the list). Tags trimmed/lowercased/deduped, max 20.
      Added simple token login (only a SHA-256 hash is stored) and a DB layer
      (SQLAlchemy; SQLite by default, PostgreSQL via DATABASE_URL).

- [x] 6. Relevance scoring
      Files: src/backend/services/scoring.py
      Do: simple keyword/tag overlap score between user interests and place
          category/name first (defer embeddings until this works)
      Check: unit test — a "coworking" place scores higher for a user
          interested in "startups" than a "restaurant" does
      Done 2026-11-21: 11 tests in tests/test_scoring.py pass. ~60 known
      interests map to category points; +2 if an interest is a whole word in
      the name/OSM type. Each score has human-readable reasons. rank_places()
      sorts by score, then distance.

- [x] 7. Combine into /nearby response
      Files: src/backend/routers/location.py (update)
      Do: /nearby now returns places sorted by relevance score
      Check: manual test with real coordinates, inspect the ranked output
      Done 2026-11-21: /nearby = fetch -> clean -> score -> sort. Interests
      from body, else from saved profile when logged in. 503 if Overpass is
      down. Real test near Shaniwar Wada (Pune) returned a sensible ranking
      in 54 s ("Captain Coffee" top for startups/coffee/reading/history).
      Tuning from that output: added historic=* (-> culture), schools ->
      "other", culture interests give event halls 1 pt not 2. Re-run after
      tuning got 503 (Overpass busy). Handled correctly. Server log had 0
      coordinates. Total tests: 64.
      Known issue: real requests take ~30-60 s because public Overpass is slow.

## Phase 2 — Opted-in people matching (NearbyConnect users only)

- [ ] 8. User location opt-in + storage
      Do: user can share last known location (with explicit consent toggle)
      Check: location only stored when consent = true; test the false case too

- [ ] 9. Nearby opted-in users
      Do: given a user, find other opted-in users within radius + overlapping
          interests
      Check: two test users with shared interest + close coordinates match;
          a far-away or no-overlap user does not

- [ ] 10. One-tap connect request (not auto-connect)
      Do: POST /connect-request creates a pending request; recipient must
          approve
      Check: request appears as "pending" until the other user approves it

## Phase 3 — Mobile app (after backend phases 1-2 are working and tested)

- [ ] 11. React Native app skeleton + GPS permission flow
- [ ] 12. Feed screen calling /nearby
- [ ] 13. Connect request UI (send/approve)
- [ ] 14. Push notification on new match / approved connection

## Explicitly deferred / out of scope for now
- Scraping individual people's social profiles — not building this, ever.
- Automated follow/connect on LinkedIn/Instagram/X — ToS violation, skip.
- Paid APIs (Google Places, Eventbrite) — swap in once free version works.
- Enterprise scaling — revisit after Phase 3 works for ~1 real user (you).

## Current status
Last done: step 7 | Next: step 8 (location opt-in + storage) | Blockers: none (note: Overpass is slow/flaky)
