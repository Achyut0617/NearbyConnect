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

- [x] 8. User location opt-in + storage
      Do: user can share last known location (with explicit consent toggle)
      Check: location only stored when consent = true; test the false case too
      Done 2026-11-21: 11 tests in tests/test_sharing.py pass. PUT/GET/DELETE
      /me/location (routers/sharing.py). consent=false erases and ignores
      sent coords; only the last location is kept; >2 h old = stale;
      coordinates never echoed back. NOTE: users table gained columns. If an
      old dev nearbyconnect.db exists, delete it (no migrations yet).

- [x] 9. Nearby opted-in users
      Do: given a user, find other opted-in users within radius + overlapping
          interests
      Check: two test users with shared interest + close coordinates match;
          a far-away or no-overlap user does not
      Done 2026-11-21: 12 tests in tests/test_people.py pass. GET
      /me/nearby-users?radius_m= (default 2000, max 5000). You must be
      sharing (fresh) to see others (409 otherwise). Returns name, shared
      interests, distance rounded UP to 100 m, never coordinates. Sorted by
      #shared interests, then distance. Stale/non-sharing users excluded.

- [x] 10. One-tap connect request (not auto-connect)
      Do: POST /connect-request creates a pending request; recipient must
          approve
      Check: request appears as "pending" until the other user approves it
      Done 2026-11-21: 12 tests in tests/test_connect.py pass (99 total).
      POST /connect-requests, GET /connect-requests (incoming/outgoing),
      POST /connect-requests/{id}/accept|decline (recipient only),
      GET /connections. No self/duplicate requests; no re-request after a
      decline. Full 2-user flow verified on a real server; 0 coords in log.

## Phase 3 — Mobile app (after backend phases 1-2 are working and tested)

- [x] 11. React Native app skeleton + GPS permission flow
      Done 2026-11-21: Expo SDK 58 + Expo Router app in src/mobile. Onboarding
      (privacy promises -> sign-up with interests -> foreground-only GPS
      permission, "Not now" allowed). Tabs: Feed/People/Requests (placeholders),
      Profile (edit interests, permission status, sign out). Token in
      expo-secure-store (localStorage on web). Checks: tsc clean, Android +
      web bundles build, expo-doctor 20/20. Backend: CORS for web (100 tests).
      Not yet run on a real phone (needs you + Expo Go).
- [x] 12. Feed screen calling /nearby
      Done 2026-11-21: src/mobile/src/app/(tabs)/index.tsx. Permission card if
      not granted; radius chips (500 m-5 km); place cards with category,
      distance, "Why this?" reasons, Open in Maps; pull-to-refresh; reloads
      when interests change; clear 503 / offline messages; ignores stale
      responses. Checks: tsc clean, Android bundle builds. Not run on a phone yet.
- [x] 13. Connect request UI (send/approve)
      Done 2026-11-21: People tab = sharing switch (off by default, confirm
      dialog says exactly what's shown), nearby matches with Connect button,
      location refreshed on open while sharing. Requests tab = incoming
      (Accept/Decline), outgoing (waiting), connections. Checks: tsc clean,
      Android bundle builds; app's api.ts ran the full 2-user flow against
      the real backend (all calls + 409/401 errors OK). Not run on a phone yet.
- [x] 14. Push notification on new match / approved connection
      Done 2026-11-21: backend stores Expo push token (PUT/DELETE
      /me/push-token), sends via Expo Push API as a background task on
      new request (to recipient) and accept (to sender); no push on decline;
      dead tokens (DeviceNotRegistered) are forgotten; failures never break
      the request. 13 new tests (113 total). Real Expo API answered a fake
      token with the exact error shape we handle. App: Profile "Turn on
      notifications", silent refresh if already allowed, tap opens Requests,
      token removed on sign out. tsc, Android + web bundles, expo-doctor 20/20.
      DECIDED NOT TO BUILD "new match" pushes: needs background location or
      server-side presence scanning, which breaks our privacy promises.
      To test on a phone you need a development build (NOT Expo Go):
        cd src/mobile && npx expo install expo-dev-client
        npx eas-cli@latest init        (adds extra.eas.projectId to app.json)
        npx eas-cli@latest build --profile development --platform android

## Phase 4 — Place intelligence + area trends + author profiling (web scraping / NLP)
Goal: a resume-grade scraping + data-cleaning + NLP pipeline. Scope: start with
Maharashtra, then widen. Build in the order Stage A -> B -> C.

### Privacy boundary for ALL of Phase 4 (do not cross)
- NO building a list of individual social accounts tied to a place, and NO
  predicting who a specific real person is. That identifies/profiles people
  who never consented — violates CLAUDE.md hard constraint #1 and the law
  (India DPDP Act 2023), and gets accounts banned by the platforms.
- Area analytics are AGGREGATE ONLY: a topic/hashtag is shown only if used by
  >= MIN_DISTINCT_AUTHORS (start at 20) different accounts. Never list account
  names, handles, or per-account data in any output.
- The profiling MODEL (Stage C) runs ONLY on: (a) public research/benchmark
  datasets whose licence allows it, and (b) a NearbyConnect user analysing
  THEIR OWN linked account with explicit consent. Never on scraped strangers.
- Scrape only via official APIs / open sources that permit it; obey robots.txt
  and rate limits; identify with a generic User-Agent (no personal info).
- Nothing from Stage B/C scraping is stored long-term: short-lived in-memory
  cache only (ties back to the "no raw history" rule).

### Stage A — Place intelligence
- [ ] 15. Place lookup from trusted sources
      Files: src/backend/services/place_intel.py
      Do: given a place name (e.g. "Loni Kalbhor, Pune"), fetch facts from
          Wikipedia + Wikidata + OSM (REST APIs). Return a clean summary:
          description, landmarks, nearby colleges/industries, known-for tags.
      Check: unit test with cached/sample API responses -> structured facts;
          a nonsense place returns "not found", not a crash.
- [ ] 16. Keyword / hashtag extraction for an area
      Files: src/backend/services/keywords.py
      Do: from the Stage-15 facts, derive ranked search terms + hashtags
          (college names, landmarks, #placename, "known-for" words). Simple
          scoring first (frequency/importance), embeddings later.
      Check: test that "Loni Kalbhor" facts yield sensible terms; dedupe works.

### Stage B — Area trend analytics (AGGREGATE ONLY: Reddit + YouTube first)
- [ ] 17. Platform clients (official APIs)
      Files: src/backend/services/sources/reddit.py, .../youtube.py
      Do: search public posts/videos by keyword/area via official APIs
          (API keys in .env, never committed). Return topics + counts only.
      Check: tests use recorded sample responses (offline); missing API key
          returns a clear "source unavailable", not a crash.
- [ ] 18. Aggregation + k-author threshold
      Files: src/backend/services/trends.py
      Do: roll results into topic counts, co-occurring hashtags, rising/falling,
          overall sentiment. DROP any topic used by < MIN_DISTINCT_AUTHORS.
          Output carries NO account identifiers.
      Check: test that a topic from 5 accounts is dropped, one from 25 is kept;
          output contains zero handles/usernames.
- [ ] 19. /area-trends endpoint + app "Area" view
      Do: GET /area-trends?place=... returns the aggregate picture; app shows it.
      Check: manual test for a Maharashtra place; inspect that it's all aggregate.

### Stage C — Author profiling model (occupation), consent/benchmark data ONLY
- [ ] 20. Feature extraction from posts (text/hashtags/timing/topics)
      Files: src/backend/services/profiling/features.py
      Do: turn a set of posts into features (topic mix, active hours, vocab,
          hashtag categories). Input is a dataset row or a consented user's own
          posts — never a scraped stranger.
      Check: unit test on sample post sets -> feature vector.
- [ ] 21. Occupation estimator v1 (explainable formula) + evaluation
      Files: src/backend/services/profiling/estimate.py
      Do: Bayes-style scoring over classes (student/teacher/researcher/
          industry/other) with per-class probabilities AND a plain "because..."
          explanation. Evaluate on a licensed public benchmark; report accuracy
          + calibration.
      Check: evaluation script prints real metrics; probabilities sum ~1.
- [ ] 22. Occupation estimator v2 (trained model) + compare
      Files: src/backend/services/profiling/model.py
      Do: logistic-regression (or similar) version; compare vs v1 on the same
          benchmark. Document which wins and why.
      Check: metrics table v1 vs v2 reproducible from a script.
- [ ] 23. Synthetic noisy-profile generator (for entity-resolution testing)
      Files: src/backend/services/profiling/synthetic.py
      Do: generate N fake profiles with typos/dupes/nicknames/missing fields
          AND known ground-truth labels, for measuring accuracy safely.
      Check: generator is seedable/reproducible; ground truth is recoverable.
- [ ] 24. Opt-in "analyse my own account" in the app
      Do: a user links THEIR account, consents, gets their own estimated
          interests/occupation + "why". Same model, with consent. Never others.
      Check: nothing runs without an explicit consent flag; test the false case.

## Explicitly deferred / out of scope for now
- Scraping individual people's social profiles — not building this, ever.
- Automated follow/connect on LinkedIn/Instagram/X — ToS violation, skip.
- Paid APIs (Google Places, Eventbrite) — swap in once free version works.
- Enterprise scaling — revisit after Phase 3 works for ~1 real user (you).

## Current status
Last done: step 14 (Phases 1-3 done). Phase 4 (steps 15-24) designed & agreed,
not started. | Next: step 15 (place lookup) when you say go; still want to test
the app on a real phone too. | Phase 4 scope: Maharashtra first. Aggregate-only
area trends (Reddit+YouTube), occupation model on consent/benchmark data only,
NO profiling of specific strangers (see Phase 4 privacy boundary above).
Known limits: Overpass slow (30-60 s) / sometimes 503; push needs a dev build;
no DB migrations; lost token = lost account | Blockers: none
