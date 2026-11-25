# Getting the API keys for Stage B (area trends)

The app works **without** these keys — the Reddit/YouTube trend features just stay
off and the endpoint says "source unavailable". Add them when you want real
area-trend data. Both are **free**.

Put the values in `src/backend/.env` (copy from `.env.example`). **Never commit `.env`.**

---

## 1. Reddit (free)

1. Log in to Reddit, then open **https://www.reddit.com/prefs/apps**
2. Scroll down, click **"are you a developer? create an app..."**
3. Fill in:
   - **name:** `nearbyconnect`
   - **type:** choose **"script"**
   - **description:** anything (e.g. "college project")
   - **about url:** leave blank
   - **redirect uri:** `http://localhost:8000`
4. Click **Create app**.
5. You now see the app box. Copy two values:
   - The string **under the app name** (that's the **client id**)
   - The value next to **"secret"** (that's the **client secret**)
6. In `src/backend/.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_secret_here
   ```

---

## 2. YouTube Data API v3 (free, needs a Google account)

1. Open **https://console.cloud.google.com/**
2. Top bar → project dropdown → **New Project** (name it `nearbyconnect`) → **Create**.
   Make sure the new project is selected.
3. Left menu → **APIs & Services → Library**.
4. Search **"YouTube Data API v3"**, open it, click **Enable**.
5. Left menu → **APIs & Services → Credentials**.
6. Click **+ Create Credentials → API key**. Copy the key it shows.
7. (Recommended) Click the key → under **API restrictions** choose
   **Restrict key → YouTube Data API v3 → Save**. This limits what the key can do.
8. In `src/backend/.env`:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

**Quota note:** the free YouTube quota is about 10,000 "units" per day, and a
search costs ~100 units, so roughly 100 searches/day. Our code searches only the
top 3 keywords per area, so that's plenty for testing.

---

## After adding keys

1. Restart the backend so it reads the new `.env`.
2. Test:
   ```
   GET http://localhost:8000/area-trends?place=Loni Kalbhor, Pune
   ```
   (needs a login token — easiest via the app, or http://localhost:8000/docs)

If a key is missing or wrong, that source is listed under `sources_skipped`
in the response instead of causing an error.

---

## 3. Geoapify (free, optional backup for places)

Used **only** when the free OpenStreetMap (Overpass) servers are all busy.
Without it, `/nearby` just says "busy, try again" like before.

1. Sign up at **https://myprojects.geoapify.com** (free plan, no card needed).
2. Create a project, then copy its **API key**.
3. In `src/backend/.env`:
   ```
   GEOAPIFY_API_KEY=your_key_here
   ```
4. Restart the backend. Nothing else changes: places come back in the same shape.
