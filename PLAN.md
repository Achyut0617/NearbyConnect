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

- [ ] 3. Place data fetch (Overpass/OSM)
      Files: src/backend/services/osm_client.py
      Do: given lat/lon/radius, call Overpass API, return raw list of nearby
          places (name, type, coordinates)
      Check: unit test with a known lat/lon (e.g. a landmark) returns >0 places

- [ ] 4. Data cleaning + validation
      Files: src/backend/services/clean.py
      Do: dedupe places, drop entries missing a name, normalize place "type"
          into a small fixed category set (food, coworking, event space, etc.)
      Check: test with deliberately messy/duplicate input, confirm output is
          deduped and categorized

- [ ] 5. User interest profile (minimal)
      Files: src/backend/models/user.py, src/backend/routers/profile.py
      Do: user can POST a list of interest tags (e.g. ["AI", "startups"])
      Check: POST then GET returns the same tags

- [ ] 6. Relevance scoring
      Files: src/backend/services/scoring.py
      Do: simple keyword/tag overlap score between user interests and place
          category/name first (defer embeddings until this works)
      Check: unit test — a "coworking" place scores higher for a user
          interested in "startups" than a "restaurant" does

- [ ] 7. Combine into /nearby response
      Files: src/backend/routers/location.py (update)
      Do: /nearby now returns places sorted by relevance score
      Check: manual test with real coordinates, inspect the ranked output

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
Last done: step 2 | Next: step 3 (place data fetch from Overpass/OSM) | Blockers: none
