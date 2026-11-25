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
| Data cleaning | Fixing or removing messy entries before using the data | Dropping places with blank names |
| De-duplication | Removing repeated copies of the same thing | Same cafe mapped as point + building |
| Haversine formula | Maths for the distance between two GPS points on a round Earth | distance_m() in clean.py |
| Normalising / categorising | Turning many detailed labels into a few simple groups | amenity=cafe and shop=coffee both become "cafe" |
| Database (DB) | A program that stores data safely so it's still there after a restart | users table with interests |
| SQLAlchemy | Python library to talk to databases; same code works for SQLite and PostgreSQL | db.py, models/user.py |
| SQLite | A tiny database kept in one file, no server needed | nearbyconnect.db during development |
| Model / table | A Python class that maps to a database table; each object is one row | `User` class -> users table |
| Token (login) | A long random secret the app sends to prove who it is | `Authorization: Bearer <token>` |
| Hash | A one-way scramble of text; you can check a match but can't reverse it | we store sha256(token), not the token |
| HTTP 401 | "Unauthorized": no token or a wrong token | GET /me without a token |
| PUT vs POST | POST usually creates something new; PUT replaces something that exists | POST /users creates; PUT /me/interests replaces |
| Fixture (pytest) | Reusable setup a test asks for by name | `client`, `make_user`, fresh DB in conftest.py |
| Relevance score | A number saying how well something matches what the user wants | coworking space = 3 points for "startups" |
| Regex word boundary (\b) | Regex rule meaning "start/end of a whole word" | "ai" matches "AI Lab" but not "Sai" |
| Sort key | The value(s) Python sorts by; a tuple sorts by the first, then the second... | (-score, distance) = best score, then nearest |
| Pipeline | Several steps chained, each feeding the next | fetch -> clean -> score -> sort in /nearby |
| HTTP 503 | "Service unavailable": try again later | /nearby when every Overpass server is busy |
| Dependency override | In tests, swap a real piece (like the internet fetch) for a fake | app.dependency_overrides[get_place_fetcher] |
| Tuning | Adjusting rules after looking at real results | schools -> "other" after seeing them rank high |
| Consent / opt-in | The user must actively say "yes" before we use their data | consent=true needed to store location |
| Data minimisation | Keep only the data you truly need, for as short as possible | only last location, stale after 2 h |
| model_validator | A Pydantic check that looks at several fields together | lat+lon required only when consent=true |
| Nullable column | A database column allowed to be empty (NULL / None) | last_lat is None when not sharing |
| Reciprocity | Rule that you only get something if you give the same | must share location to see others |
| Rounding for privacy | Making a number less exact so it can't pinpoint someone | 330 m shown as "400 m" |
| Set intersection | Items that are in both lists | shared interests between two users |
| HTTP 409 | "Conflict": the request clashes with the current state | asking for nearby users while not sharing |
| Foreign key | A column pointing to a row in another table | connect_requests.from_user_id -> users.id |
| State machine | Something that moves between fixed states by fixed rules | pending -> accepted / declined, never back |
| HTTP 403 vs 404 | 403 = "you're not allowed"; 404 = "not found" (also used so strangers can't tell a thing exists) | sender accepting own request = 403; outsider = 404 |
| Hook | An empty function called at a key moment so features can plug in later | on_request_accepted() for push notifications |
| Expo | Toolkit that makes React Native apps easier to build and test | `npx expo start`, scan the QR in Expo Go |
| Expo Go | Phone app that runs your project without building it yourself | Test Steps 11-13 instantly |
| Development build | Your own custom version of the app, needed for some native features | Push notifications (Step 14) |
| Expo Router | Navigation where each file in src/app is a screen | src/app/(tabs)/profile.tsx = Profile tab |
| TypeScript | JavaScript with types; catches mistakes before running | `npx tsc --noEmit` |
| React context | Share data (like the login) with every screen without passing it down by hand | SessionProvider / useSession() |
| Secure storage | Encrypted storage on the phone for secrets | login token in expo-secure-store |
| Foreground permission | Location only while the app is open | requestForegroundPermissionsAsync() |
| CORS | Browser rule: a web page may only call other servers that allow it | backend allows the web app |
| Bundle | All the app's code packed into one file the phone runs | `npx expo export` builds it |
| FlatList | React Native list that only draws the rows on screen, so long lists stay fast | place cards in the Feed |
| useEffect | Run code when a screen opens or when certain values change | reload places when radius changes |
| Pull-to-refresh | Drag the list down to reload | RefreshControl in the Feed |
| Stale response | An older, slower request answering after a newer one | requestId ref ignores old answers |
| useFocusEffect | Run code every time a tab comes back on screen | reload requests when opening the tab |
| Switch | On/off toggle control | "Share my location" |
| Confirmation dialog | Ask "are you sure?" before something important | before turning on location sharing |
| Integration check | Testing two real parts together, not with fakes | app's api.ts against the running backend |
| Push notification | A message the server sends to a phone even when the app is closed | "Asha wants to connect" |
| Expo push token | The phone's "address" for notifications | ExponentPushToken[...] |
| Background task | Work done AFTER the reply is sent, so the user doesn't wait | sending the push in FastAPI |
| monkeypatch | pytest tool to temporarily replace a function in a test | fake send_to_expo in conftest.py |
| Web scraping | Reading data from web pages/APIs automatically | place_intel, reddit, youtube clients |
| Aggregate / k-anonymity | Only report a group stat if >= k people share it | topic shown only if >= 20 authors |
| Feature extraction | Turning raw text into numbers a model can use | features.py |
| Naive Bayes | Combine independent clues into a probability | estimate.py v1 formula |
| Logistic regression | A trained model that predicts class probabilities | model.py v2 (scikit-learn) |
| Calibration (ECE) | Are the confidence numbers honest? | measured in train_profiling.py |
| Synthetic data | Fake data with known answers, to measure accuracy safely | synthetic.py |
| Docker | Pack the app so it runs the same anywhere | Dockerfile, docker-compose.yml |
| CI (GitHub Actions) | Auto-run tests on every push | .github/workflows/ci.yml |
| Cache + TTL | Keep a recent answer for a short time (Time To Live) so repeats are instant | place_cache.py, 10 min |
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

- 2026-11-21: Problem: first real /nearby ranking had schools and wedding
  halls near the top, and Shaniwar Wada was missing | Cause: rules were
  guessed without real data; forts use the OSM key `historic`, which we
  didn't ask for | Fix: added `historic`, schools -> other, smaller
  history -> event hall points; added tests for each | Lesson: unit tests
  prove the code does what you said; only real data shows whether what you
  said was a good idea.

- 2026-11-25: Concept: fallback (backup) provider | When the main service
  (Overpass) fails, try a second one (Geoapify) that returns the SAME data
  shape, so the rest of the code never knows which one answered. Only
  "service is down" errors trigger the backup; real bugs (e.g. ValueError)
  are not hidden. | Lesson: an adapter that converts each provider into
  one common shape is what makes swapping providers cheap.

## Still confusing
- (fill in as we go)
