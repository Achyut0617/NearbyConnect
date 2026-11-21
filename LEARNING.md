# What I learned

## Words / concepts
| Word | Meaning in my words | Example |
|------|---------------------|---------|
| FastAPI | Python web framework for building APIs quickly | Defines /nearby endpoint |
| Overpass API | Free query service for OpenStreetMap data | Ask it for all cafes within 2km |
| pgvector | Postgres extension for storing/searching embeddings | Used later for interest-matching |
| Embedding | A list of numbers representing meaning of text, so similar things are "close" | "startups" and "entrepreneurship" end up near each other |
| ToS (Terms of Service) | The rules a platform sets for using its service/API | LinkedIn's ToS bans automated connection requests |
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
