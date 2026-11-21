# What I learned

## Words / concepts
| Word | Meaning in my words | Example |
|------|---------------------|---------|
| FastAPI | Python web framework for building APIs quickly | Defines /nearby endpoint |
| Overpass API | Free query service for OpenStreetMap data | Ask it for all cafes within 2km |
| pgvector | Postgres extension for storing/searching embeddings | Used later for interest-matching |
| Embedding | A list of numbers representing meaning of text, so similar things are "close" | "startups" and "entrepreneurship" end up near each other |
| ToS (Terms of Service) | The rules a platform sets for using its service/API | LinkedIn's ToS bans automated connection requests |
| Pydantic model | A Python class describing the shape of incoming data; FastAPI checks requests against it | `NearbyRequest` has lat, lon, radius_m |
| Field(ge=, le=, gt=) | Rules on a value: ge = "greater or equal", le = "less or equal", gt = "greater than" | `lat` must be ge=-90, le=90 |
| HTTP 422 | "Unprocessable" — the request arrived but the data broke a rule | Sending lat=200 |
| Router | A group of related endpoints in its own file, plugged into the main app | routers/location.py |
| pytest + TestClient | Run the app inside a test without starting a real server | tests/test_location.py |
| Rate limiting | A platform capping how many requests you can make | Why we can't mass-scrape without getting blocked/banned |

## Problems I solved
- 2026-11-21 — Problem: pip showed a dependency conflict warning (sse-starlette
  vs starlette) | Cause: an unrelated package already installed on the
  machine wants a newer starlette than FastAPI pulled in | Fix: ignored it —
  it doesn't affect our app, confirmed by actually running the server and
  hitting /health successfully | Lesson: a pip warning isn't automatically a
  real problem; test the actual thing you care about before worrying.

## Still confusing
- (fill in as we go)
