# NearbyConnect

[![CI](https://github.com/Achyut0617/nearbyconnect/actions/workflows/ci.yml/badge.svg)](https://github.com/Achyut0617/nearbyconnect/actions/workflows/ci.yml)

Location-aware networking + an area-intelligence and author-profiling data
pipeline. Built step by step; every step is tested.

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (SQLite dev / PostgreSQL prod)
- **Mobile/web app:** React Native (Expo SDK 58, Expo Router, TypeScript)
- **Data/ML:** OpenStreetMap, Wikipedia/Wikidata, Reddit & YouTube (official
  APIs), scikit-learn for the occupation-profiling model

## What it does

### Core app (Phases 1–3)
- `/nearby`: ranks real nearby places against your interests (OpenStreetMap).
- Opt-in people matching **among registered users only** — share location, see
  others with shared interests (rough distance only), send/accept connect
  requests, get push notifications.

### Data pipeline (Phase 4)
- **Stage A — Place intelligence:** given a place (e.g. "Loni Kalbhor, Pune"),
  pull trusted facts (Wikipedia/Wikidata/OSM) and derive area keywords/hashtags.
- **Stage B — Area trends (aggregate only):** search those terms on Reddit and
  YouTube and report **topics and counts**, never individuals. A topic appears
  only if ≥ 20 distinct accounts used it.
- **Stage C — Author profiling (consent/benchmark only):** a scikit-learn model
  that estimates occupation (student / teacher / researcher / industry / other)
  with probabilities and plain-English reasons. Trained and measured on
  **synthetic labelled data**; usable on a user's **own** account with consent.

### Privacy boundaries (enforced in code, see `DECISIONS.md`)
- No scraping or profiling of specific non-consenting people.
- Area analytics are aggregate-only (k-author threshold).
- No raw location history; coordinates never logged; tokens stored hashed.

## Run it

### Backend (local, SQLite)
```bash
cd src/backend
python -m venv venv                   # optional: keep packages separate
pip install -r requirements.txt
uvicorn main:app --reload             # http://localhost:8000  (docs at /docs)
pytest -q                             # run the test suite
```

### Backend (Docker + PostgreSQL)
```bash
docker compose up --build             # API on http://localhost:8000
```

### App
```bash
cd src/mobile
npm install
npx expo start                        # press w for web, or scan the QR in Expo Go
```

### Train / evaluate the profiling model
```bash
cd src/backend
python -m scripts.train_profiling --n 5000
# prints a v1-formula vs v2-model accuracy + calibration comparison,
# and saves the trained model for /me/analyze to use
```

## API keys
Stage B (Reddit/YouTube) is optional and free. Setup steps: `docs/API_KEYS.md`.
Without keys, those sources are simply skipped.

## Project layout
```
src/backend/
  main.py                 FastAPI app
  routers/                HTTP endpoints (nearby, profile, people, connect,
                          sharing, push, area, profiling)
  services/               logic: osm_client, clean, scoring, matching, push
    place_intel, keywords, trends, sources/   (Stage A+B)
    profiling/            (Stage C: synthetic, features, estimate, model)
  scripts/train_profiling.py
  tests/                  160+ tests
src/mobile/               Expo app (src/app = screens, src/lib = logic)
.github/workflows/ci.yml  backend tests + mobile typecheck + docker build
```

See `PLAN.md` for the step-by-step build log and `DECISIONS.md` for why things
are the way they are.
