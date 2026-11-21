# Project: NearbyConnect

## What this project does
Location-aware networking app. As the user moves, it pulls public data about
the surrounding area (places, events, opportunities) from legitimate APIs,
scores it against the user's stated interests/goals, and surfaces a ranked
feed of suggestions. Connections to other people happen only between users
who have opted into the app and explicitly tap "Connect" — no scraping of
individuals, no automated follow/connect on any third-party platform.

## Tech stack
- Backend: Python 3.12, FastAPI
- DB: PostgreSQL + pgvector (for interest/embedding matching)
- Mobile: React Native (Expo SDK 58, Expo Router, TypeScript)
- Data sources (v1, free tier): OpenStreetMap/Nominatim + Overpass API for
  places; user-submitted profiles for the "people" side
- Later (paid, deferred): Google Places API, Eventbrite/Meetup API

## Hard constraints (do not violate)
- NEVER scrape social media profiles or personal data about non-users.
- NEVER automate follow/connect/DM actions on a third-party platform
  (LinkedIn, Instagram, X, etc.) — those ToS violations get accounts banned
  and the app sued. All third-party social actions are manual, user-initiated.
- All "people" matching happens only among NearbyConnect's own opted-in users.
- Location data is sensitive: never log raw GPS history beyond what's needed
  for the current session; get explicit consent before using GPS at all.

## How to run
- Backend install: `cd src/backend && pip install -r requirements.txt`
- Backend run: `uvicorn main:app --reload`
  (for a phone on the same Wi-Fi: `uvicorn main:app --reload --host 0.0.0.0`)
- Test: `pytest -q` (from src/backend)
- Mobile install: `cd src/mobile && npm install`
- Mobile config: copy `src/mobile/.env.example` to `src/mobile/.env` and set
  EXPO_PUBLIC_API_URL to your computer's Wi-Fi IP, e.g. http://192.168.1.10:8000
- Mobile run: `npx expo start` (scan QR with Expo Go), or press `w` for web
- Mobile checks: `npx tsc --noEmit` and `npx expo-doctor`
- Add mobile packages ONLY with `npx expo install <pkg>` (SDK-matched versions)

## Rules for Claude
- I am a beginner. Explain in simple English, one step at a time.
- Work one step at a time from PLAN.md. Don't jump ahead.
- Always run tests/commands after a change and show me the real output.
- Update PLAN.md and LEARNING.md after each step.
- Flag immediately if a requested feature would require scraping individuals
  or automating third-party platform actions — suggest the compliant
  alternative instead of silently building the risky version.
