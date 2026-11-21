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
| HTTP 504 | "Gateway timeout": the server is too busy or slow to answer | Overpass replied 504 when overloaded |
| Timeout | The longest we'll wait for an answer before giving up | 25 s per Overpass server |
| Fallback | If plan A fails, automatically try plan B | Try the next Overpass server |
| Mock / fake server | A pretend server inside a test, so tests run offline and predictably | httpx.MockTransport in test_osm_client.py |
| pytest marker | A label on a test so you can choose to run or skip it | @pytest.mark.network, run with `pytest -m network` |
| Rate limiting | A platform capping how many requests you can make | Why we can't mass-scrape without getting blocked/banned |

## Problems I solved
- 2026-11-21 — Problem: pip showed a dependency conflict warning (sse-starlette
  vs starlette) | Cause: an unrelated package already installed on the
  machine wants a newer starlette than FastAPI pulled in | Fix: ignored it —
  it doesn't affect our app, confirmed by actually running the server and
  hitting /health successfully | Lesson: a pip warning isn't automatically a
  real problem; test the actual thing you care about before worrying.

- 2026-11-21: Problem: live Overpass test failed (ReadTimeout / HTTP 504
  from all 3 servers) | Cause: the free public Overpass servers were
  overloaded; openstreetmap.org itself loaded fine, so it wasn't my internet
  | Fix: code now tries several servers and raises a clear error; offline
  tests use a fake server; live test is opt-in and re-run later | Lesson:
  free shared services go down. Always plan for "the other server didn't
  answer", and keep your normal tests independent of the internet.

## Still confusing
- (fill in as we go)
